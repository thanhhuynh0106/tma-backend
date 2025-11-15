const express = require("express");
const router = express.Router();
const {
  createTeam,
  getAllTeams,
  getTeamById,
  updateTeam,
  deleteTeam,
  addMember,
  removeMember,
  assignTeamLead,
} = require("../controllers/teamController");
const { protect, authorize } = require("../middleware/auth");
const { USER_ROLES } = require("../utils/constants");

router.post("/", protect, authorize(USER_ROLES.HR_MANAGER), createTeam);
router.get("/", protect, authorize(USER_ROLES.HR_MANAGER), getAllTeams);
router.get("/:id", protect, authorize(USER_ROLES.HR_MANAGER), getTeamById);
router.put("/:id", protect, authorize(USER_ROLES.HR_MANAGER), updateTeam);
router.delete("/:id", protect, authorize(USER_ROLES.HR_MANAGER), deleteTeam);

router.post(
  "/:id/members",
  protect,
  authorize(USER_ROLES.TEAM_LEAD, USER_ROLES.HR_MANAGER),
  addMember
);

router.delete(
  "/:id/members/:userId",
  protect,
  authorize(USER_ROLES.TEAM_LEAD, USER_ROLES.HR_MANAGER),
  removeMember
);

router.put(
  "/:id/leader",
  protect,
  authorize(USER_ROLES.HR_MANAGER),
  assignTeamLead
);

module.exports = router;
