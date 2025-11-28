const Team = require("../models/Team");
const User = require("../models/User");
const Task = require("../models/Task");

/**
 *  Create a new team
 *  @param {Object} teamData
 *  @returns {Object}
 */

const createTeam = async (teamData) => {
  const { name, description, leaderId } = teamData;

  const existingTeam = await Team.findOne({ name });
  if (existingTeam) {
    throw new Error("Team name already exists");
  }

  const leader = await User.findById(leaderId);
  if (!leader) {
    throw new Error("Leader user not found");
  }

  const team = await Team.create({
    name,
    description: description || "",
    leaderId,
    members: [leaderId],
    createdAt: new Date(),
    updatedAt: new Date(),
  });

  // Update leader's teamId
  await User.findByIdAndUpdate(leaderId, { teamId: team._id }, { new: true });

  return team.populate("leaderId", "profile.fullName email");
};

/**
 * Get all teams with pagination
 * @param {Number} page
 * @param {Number} limit
 * @returns {Object}
 */

const getAllTeams = async (page = 1, limit = 10) => {
  const skip = (page - 1) * limit;

  const total = await Team.countDocuments();
  const teams = await Team.find()
    .skip(skip)
    .limit(limit)
    .populate("leaderId", "profile.fullName email")
    .populate("memberIds", "profile.fullName email role")
    .sort({ createdAt: -1 });

  return {
    teams,
    pagination: {
      current: page,
      total: Math.ceil(total / limit),
      count: teams.length,
      totalRecords: total,
    },
  };
};

/**
 * Get team by ID with all details
 * @param {String} teamId
 * @returns {Object|null}
 */

const getTeamById = async (teamId) => {
  return await Team.findById(teamId)
    .populate("leaderId", "profile.fullName email phone")
    .populate("memberIds", "profile.fullName email role department");
};

/**
 * Update team info
 * @param {String} teamId
 * @param {Object} updateData
 * @returns {Object}
 */

const updateTeam = async (teamId, updateData) => {
  const { name, description, leaderId } = updateData;

  if (name) {
    const existingTeam = await Team.findOne({ name, _id: { $ne: teamId } });
    if (existingTeam) {
      throw new Error("Team name already exists");
    }
  }

  if (leaderId) {
    const leader = await User.findById(leaderId);
    if (!leader) {
      throw new Error("Team leader not found");
    }

    const team = await Team.findById(teamId);
    if (!team.memberIds.includes(leaderId)) {
      team.memberIds.push(leaderId);
    }
  }

  const team = await Team.findByIdAndUpdate(
    teamId,
    {
      ...(name && { name }),
      ...(description && { description }),
      ...(leaderId && { leaderId }),
      updatedAt: new Date(),
    },
    { new: true, runValidators: true }
  )
    .populate("leaderId", "profile.fullName email")
    .populate("memberIds", "profile.fullName email");

  return team;
};

/**
 * Delete (soft) team by ID
 * @param {String} teamId
 * @returns {Object}
 */

const deleteTeam = async (teamId) => {
  const team = await Team.findById(teamId);
  if (!team) {
    throw new Error("Team not found");
  }

  // Check if team has active tasks (if Task model exists)
  const activeTasks = await Task.findOne({
    teamId,
    status: { $ne: "completed" },
  });
  if (activeTasks) {
    throw new Error("Cannot delete team with active tasks");
  }

  // Remove teamId from all members
  await User.updateMany({ teamId }, { $unset: { teamId: 1 } });

  // Delete team
  return await Team.findByIdAndDelete(teamId);
};

/**
 * Add members to a team
 * @param {String} teamId
 * @param {String} userIds - Array of user IDs
 * @returns {Object}
 */

const addMember = async (teamId, userId) => {
  const team = await Team.findById(teamId);
  if (!team) {
    throw new Error("Team not found");
  }

  const user = await User.findById(userId);
  if (!user) {
    throw new Error("User not found");
  }

  if (team.memberIds.includes(userId)) {
    throw new Error("User already in this team");
  }

  team.memberIds.push(userId);
  await team.save();

  await User.findByIdAndUpdate(userId, { teamId }, { new: true });

  const populatedTeam = await Team.findById(team._id)
    .populate("leaderId", "profile.fullName email")
    .populate("memberIds", "profile.fullName email role");

  return populatedTeam;
};

/**
 * Remove member from a team
 * @param {String} teamId
 * @param {String} userId
 * @returns {Object}
 */

const removeMember = async (teamId, userId) => {
  const team = await Team.findById(teamId);
  if (!team) {
    throw new Error("Team not found");
  }

  if (team.leaderId.toString() === userId) {
    throw new Error(
      "Cannot remove the team leader from the team. Assign a new leader before removing."
    );
  }

  team.memberIds = team.memberIds.filter((id) => id.toString() !== userId);
  await team.save();

  await User.findByIdAndUpdate(userId, { $unset: { teamId: 1 } });

  return Team.findById(team._id)
    .populate("leaderId", "profile.fullName email")
    .populate("memberIds", "profile.fullName email role");
};

/**
 * Assign new team leader
 * @param {String} teamId
 * @param {String} newLeaderId
 * @returns {Object}
 */
const assignTeamLead = async (teamId, newLeaderId) => {
  const team = await Team.findById(teamId);
  if (!team) {
    throw new Error("Team not found");
  }

  const newLeader = await User.findById(newLeaderId);
  if (!newLeader) {
    throw new Error("New team leader not found");
  }

  // Check if newLeader is already in team
  if (!team.memberIds.includes(newLeaderId)) {
    team.memberIds.push(newLeaderId);
  }

  // Get current leader ID
  const currentLeaderId = team.leaderId.toString();

  // Update roles
  // 1. Change current leader to employee
  if (currentLeaderId !== newLeaderId) {
    await User.findByIdAndUpdate(
      currentLeaderId,
      { role: "employee" },
      { new: true }
    );
  }

  // 2. Change new leader to team_lead
  await User.findByIdAndUpdate(
    newLeaderId,
    { role: "team_lead" },
    { new: true }
  );

  // 3. Update team
  team.leaderId = newLeaderId;
  await team.save();

  return await Team.findById(team._id)
    .populate("leaderId", "profile.fullName email role")
    .populate("memberIds", "profile.fullName email role");
};

/**
 * Get all members of a team
 * @param {String} teamId
 * @returns {Array}
 */

const getTeamMembers = async (teamId) => {
  const members = await User.find({ teamId })
    .select("_id email role department profile");

  return members;
};

const getAllMembers = async () => {
  return await User.find()
    .select("_id email role department profile");
};

module.exports = {
  createTeam,
  getAllTeams,
  getTeamById,
  updateTeam,
  deleteTeam,
  addMember,
  removeMember,
  assignTeamLead,
  getTeamMembers,
  getAllMembers
};
