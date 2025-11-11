const User = require("../models/User");
const Team = require("../models/Team");
const { hashPassword } = require("../services/authService");
const { sendTokenResponse } = require("../config/jwt");

/**
 * @desc    Register user & get token
 * @route   POST /api/auth/register
 * @access  Public
 */
const register = async (req, res) => {
  try {
    const { email, password, role, profile } = req.body;

    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({
        success: false,
        error: "Email already registered",
      });
    }

    const hashedPassword = await hashPassword(password);

    const user = await User.create({
      email,
      password: hashedPassword,
      role: role || "employee",
      profile: {
        fullName: profile.fullName,
        employeeId: profile.employeeId,
        department: profile.department || null,
        position: profile.position || null,
        phone: profile.phone || null,
        avatar: profile.avatar || null,
      },
      teamId: null,
      managerId: null,
      isActive: true,
      leaveBalance: new Map([["2025", { total: 12, used: 0, remaining: 12 }]]),
    });

    sendTokenResponse(user, 201, res);
  } catch (error) {
    console.error("Register error:", error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};

/**
 * @desc    Login user
 * @route   POST /api/auth/login
 * @access  Public
 */
const login = async (req, res) => {
  try {
    const { email, password } = req.body;

    const user = await User.findOne({ email }).select("+password");

    if (!user) {
      return res.status(401).json({
        success: false,
        error: "Invalid credentials",
      });
    }

    const { comparePassword } = require("../services/authService");
    const isMatch = await comparePassword(password, user.password);

    if (!isMatch) {
      return res.status(401).json({
        success: false,
        error: "Invalid credentials",
      });
    }

    if (!user.isActive) {
      return res.status(401).json({
        success: false,
        error: "Account is deactivated",
      });
    }

    sendTokenResponse(user, 200, res);
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};

/**
 * @desc    Get current logged in user
 * @route   GET /api/auth/me
 * @access  Private
 */
const getMe = async (req, res) => {
  try {
    const user = await User.findById(req.user._id)
      .populate("teamId", "name")
      .populate("managerId", "email profile.fullName");

    res.json({
      success: true,
      data: user,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};

/**
 * @desc Update user profile
 * @route PUT /api/auth/profile
 * @access Private
 */
const updateProfile = async (req, res) => {
  try {
    const userId = req.user._id;
    const { fullName, department, position, phone, avatar } = req.body;

    const updateFields = {};
    if (fullName !== undefined)
      updateFields["profile.fullName"] = fullName.trim();
    if (department !== undefined)
      updateFields["profile.department"] = department;
    if (position !== undefined) updateFields["profile.position"] = position;
    if (phone !== undefined) updateFields["profile.phone"] = phone;
    if (avatar !== undefined) updateFields["profile.avatar"] = avatar;

    const user = await User.findByIdAndUpdate(
      userId,
      { $set: updateFields },
      { new: true, runValidators: true }
    );

    res.status(200).json({
      success: true,
      message: "Profile updated successfully",
      data: user,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};

module.exports = {
  register,
  login,
  getMe,
  updateProfile,
};
