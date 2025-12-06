const Task = require('../models/Task');
const User = require('../models/User');
const {
  canUserAccessTask,
  canCreateOrAssignTask,
  canUpdateTaskStatus,
  validateTaskData,
  checkIfOverdue,
  calculateProgress,
  getTaskStats
} = require('../services/taskService');
const {
  notifyTaskAssigned,
  notifyTaskUpdated,
  notifyCommentAdded
} = require('../services/notificationService');
const { getFileUrl, deleteFile, getOriginalFilename } = require('../middleware/upload');


/**
 * @desc    Create new task
 * @route   POST /api/tasks
 * @access  Private (Team Lead, HR Manager)
 */
const createTask = async (req, res) => {
  try {
    const { title, description, assignedTo, teamId, priority = 'medium', dueDate, startDate, tags = [], attachments = [], comments = [] } = req.body;

    if (!canCreateOrAssignTask(req.user)) {
      return res.status(403).json({
        success: false,
        error: 'Only Team Lead or HR Manager can create tasks'
      });
    }

    const validation = validateTaskData({ title, assignedTo, teamId, dueDate, startDate });

    if (!validation.valid) {
      return res.status(400).json({
        success: false,
        error: validation.message
      });
    }

    const task = await Task.create({
      title: title.trim(),
      description: description || '',
      assignedBy: req.user._id,
      assignedTo,
      teamId,
      priority,
      status: 'todo',
      dueDate: dueDate || null,
      startDate: startDate || null,
      tags,
      attachments,
      comments,
      progress: 0
    });

    // Notify assignees
    for (const userId of assignedTo) {
      if (userId.toString() !== req.user._id.toString()) {
        await notifyTaskAssigned(task, userId);
      }
    }

    await task.populate([
      { path: 'assignedBy', select: 'profile.fullName email' },
      { path: 'assignedTo', select: 'profile.fullName email' },
      { path: 'teamId', select: 'name' }
    ]);

    res.status(201).json({
      success: true,
      data: task
    });
  } catch (error) {
    console.error('Create task error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

/**
 * @desc    Get all tasks with filters
 * @route   GET /api/tasks
 * @access  Private (HR Manager, Team Lead)
 */
const getAllTasks = async (req, res) => {
  try {
    const { page = 1, limit = 10, status, priority, teamId, search } = req.query;
    const query = { status: { $ne: 'deleted' } };

    // Only HR Manager and Team Lead can view all tasks
    if (req.user.role === 'hr_manager') {
      // HR Manager: see all tasks, optionally filter by teamId
      if (teamId) {
        query.teamId = teamId;
      }
    } else if (req.user.role === 'team_lead') {
      // Team Lead: see only tasks in their team
      if (!req.user.teamId) {
        return res.json({ 
          success: true, 
          data: [], 
          pagination: { current: 1, total: 0, count: 0 } 
        });
      }
      query.teamId = req.user.teamId;
    } else {
      // Employee: not allowed - use /api/tasks/my instead
      return res.status(403).json({
        success: false,
        error: 'Only HR Manager and Team Lead can view all tasks. Use /api/tasks/my for your assigned tasks.'
      });
    }

    if (status) query.status = status;
    if (priority) query.priority = priority;
    if (search) query.title = { $regex: search.trim(), $options: 'i' };

    const skip = (page - 1) * limit;
    const total = await Task.countDocuments(query);

    const tasks = await Task.find(query)
      .populate('assignedBy', 'profile.fullName email avatar')
      .populate('assignedTo', 'profile.fullName email avatar')
      .populate('teamId', 'name')
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(parseInt(limit));

    const enrichedTasks = tasks.map(t => ({
      ...t.toObject(),
      overdue: checkIfOverdue(t),
      progress: calculateProgress(t)
    }));

    res.json({
      success: true,
      count: tasks.length,
      total,
      page: parseInt(page),
      pages: Math.ceil(total / limit),
      data: enrichedTasks
    });
  } catch (error) {
    console.error('Get all tasks error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

/**
 * @desc    Get task by ID
 * @route   GET /api/tasks/:id
 * @access  Private
 */
const getTaskById = async (req, res) => {
  try {
    const task = await Task.findById(req.params.id)
      .populate('assignedBy', 'profile.fullName email avatar')
      .populate('assignedTo', 'profile.fullName email avatar')
      .populate('teamId', 'name')
      .populate('comments.userId', 'profile.fullName avatar email');

    if (!task || task.status === 'deleted') {
      return res.status(404).json({
        success: false,
        error: 'Task not found'
      });
    }
    console.log("task.assignedTo (after populate):", task.assignedTo);
    if (!canUserAccessTask(req.user, task)) {
      return res.status(403).json({
        success: false,
        error: 'Not authorized to view this task'
      });
    }

    res.json({
      success: true,
      data: {
        ...task.toObject(),
        overdue: checkIfOverdue(task),
        progress: calculateProgress(task)
      }
    });
  } catch (error) {
    console.error('Get task by ID error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

/**
 * @desc    Update task (title, dates, priority, etc.)
 * @route   PUT /api/tasks/:id
 * @access  Private (Creator, Assignee, HR)
 */
const updateTask = async (req, res) => {
  try {
    const task = await Task.findById(req.params.id);
    if (!task || task.status === 'deleted') {
      return res.status(404).json({ success: false, error: 'Task not found' });
    }

    if (!canUserAccessTask(req.user, task)) {
      return res.status(403).json({ success: false, error: 'Not authorized' });
    }

    const allowedFields = ['title', 'description', 'priority', 'dueDate', 'startDate', 'tags'];
    allowedFields.forEach(field => {
      if (req.body[field] !== undefined) task[field] = req.body[field];
    });

    await task.save();

    if (req.body.priority || req.body.dueDate) {
      await notifyTaskUpdated(task, req.user._id);
    }

    await task.populate('assignedBy assignedTo teamId comments.userId');

    res.json({
      success: true,
      data: { ...task.toObject(), progress: calculateProgress(task) }
    });
  } catch (error) {
    console.error('Update task error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
};

/**
 * @desc    Delete task (soft delete)
 * @route   DELETE /api/tasks/:id
 * @access  Private (Creator or HR)
 */
const deleteTask = async (req, res) => {
  try {
    const task = await Task.findById(req.params.id);
    if (!task) {
      return res.status(404).json({ success: false, error: 'Task not found' });
    }

    const canDelete = req.user.role === 'hr_manager' || task.assignedBy.toString() === req.user._id.toString();
    if (!canDelete) {
      return res.status(403).json({ success: false, error: 'Permission denied' });
    }

    task.status = 'deleted';
    await task.save();

    res.json({ success: true, message: 'Task deleted successfully' });
  } catch (error) {
    console.error('Delete task error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
};

/**
 * @desc    Assign task to users
 * @route   POST /api/tasks/:id/assign
 * @access  Private (Team Lead, HR)
 */
const assignTask = async (req, res) => {
  try {
    const { assignedTo } = req.body;

    if (!canCreateOrAssignTask(req.user)) {
      return res.status(403).json({
        success: false,
        error: 'Only Team Lead or HR Manager can assign tasks'
      });
    }

    if (!Array.isArray(assignedTo) || assignedTo.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'At least one assignee is required'
      });
    }

    const task = await Task.findById(req.params.id);
    if (!task || task.status === 'deleted') {
      return res.status(404).json({ success: false, error: 'Task not found' });
    }

    const newAssignees = assignedTo.filter(id => !task.assignedTo.includes(id));
    task.assignedTo = assignedTo;
    await task.save();

    // Notify new assignees
    for (const userId of newAssignees) {
      if (userId.toString() !== req.user._id.toString()) {
        await notifyTaskAssigned(task, userId);
      }
    }

    await task.populate('assignedBy assignedTo teamId');

    res.json({
      success: true,
      message: 'Task assigned successfully',
      data: task
    });
  } catch (error) {
    console.error('Assign task error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
};

/**
 * @desc    Update task status
 * @route   PUT /api/tasks/:id/status
 * @access  Private (Assignee, Creator, HR)
 */
const updateTaskStatus = async (req, res) => {
  try {
    const { status } = req.body;

    if (!['todo', 'in_progress', 'done'].includes(status)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid status. Must be: todo, in_progress, or done'
      });
    }

    const task = await Task.findById(req.params.id);
    if (!task || task.status === 'deleted') {
      return res.status(404).json({ success: false, error: 'Task not found' });
    }

    if (!canUpdateTaskStatus(req.user, task)) {
      return res.status(403).json({ success: false, error: 'Not authorized' });
    }

    task.status = status;
    
    // Auto-update progress based on status
    if (status === 'done') {
      task.progress = 100;
    } else if (status === 'in_progress') {
      task.progress = Math.max(50, task.progress);
    }

    await task.save();
    await notifyTaskUpdated(task, req.user._id);

    await task.populate('assignedBy assignedTo teamId');

    res.json({
      success: true,
      message: 'Task status updated',
      data: { ...task.toObject(), progress: calculateProgress(task) }
    });
  } catch (error) {
    console.error('Update task status error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
};

/**
 * @desc    Update task progress
 * @route   PUT /api/tasks/:id/progress
 * @access  Private (Assignee, Creator, HR)
 */
const updateTaskProgress = async (req, res) => {
  try {
    const { progress } = req.body;

    if (progress === undefined || typeof progress !== 'number' || progress < 0 || progress > 100) {
      return res.status(400).json({
        success: false,
        error: 'Progress must be a number between 0 and 100'
      });
    }

    const task = await Task.findById(req.params.id);
    if (!task || task.status === 'deleted') {
      return res.status(404).json({ success: false, error: 'Task not found' });
    }

    if (!canUpdateTaskStatus(req.user, task)) {
      return res.status(403).json({ success: false, error: 'Not authorized' });
    }

    task.progress = progress;

    // Auto-update status based on progress
    if (progress === 100 && task.status !== 'done') {
      task.status = 'done';
    } else if (progress > 0 && task.status === 'todo') {
      task.status = 'in_progress';
    }

    await task.save();

    await task.populate('assignedBy assignedTo teamId');

    res.json({
      success: true,
      message: 'Task progress updated',
      data: { ...task.toObject(), progress: calculateProgress(task) }
    });
  } catch (error) {
    console.error('Update task progress error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
};

/**
 * @desc    Get tasks assigned to current user
 * @route   GET /api/tasks/my
 * @access  Private
 */
const getMyTasks = async (req, res) => {
  try {
    const { page = 1, limit = 10, status, priority } = req.query;
    const query = {
      assignedTo: req.user._id,
      status: { $ne: 'deleted' }
    };

    if (status) query.status = status;
    if (priority) query.priority = priority;

    const skip = (page - 1) * limit;
    const total = await Task.countDocuments(query);

    const tasks = await Task.find(query)
      .populate('assignedBy assignedTo teamId', 'profile.fullName email name')
      .sort({ dueDate: 1 })
      .skip(skip)
      .limit(parseInt(limit));

    res.json({
      success: true,
      count: tasks.length,
      total,
      page: parseInt(page),
      pages: Math.ceil(total / limit),
      data: tasks.map(t => ({
        ...t.toObject(),
        overdue: checkIfOverdue(t),
        progress: calculateProgress(t)
      }))
    });
  } catch (error) {
    console.error('Get my tasks error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

/**
 * @desc    Get team tasks
 * @route   GET /api/tasks/team/:teamId
 * @access  Private
 */
const getTeamTasks = async (req, res) => {
  try {
    const { teamId } = req.params;
    const { page = 1, limit = 10, status } = req.query;

    const query = {
      teamId,
      status: { $ne: 'deleted' }
    };

    if (status) query.status = status;

    const skip = (page - 1) * limit;
    const total = await Task.countDocuments(query);

    const tasks = await Task.find(query)
      .populate('assignedBy assignedTo teamId', 'profile.fullName email name')
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(parseInt(limit));

    res.json({
      success: true,
      count: tasks.length,
      total,
      page: parseInt(page),
      pages: Math.ceil(total / limit),
      data: tasks.map(t => ({
        ...t.toObject(),
        overdue: checkIfOverdue(t),
        progress: calculateProgress(t)
      }))
    });
  } catch (error) {
    console.error('Get team tasks error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

/**
 * @desc    Add comment to task
 * @route   POST /api/tasks/:id/comments
 * @access  Private
 */
const addComment = async (req, res) => {
  try {
    const { text } = req.body;
    if (!text?.trim()) {
      return res.status(400).json({ success: false, error: 'Comment text is required' });
    }

    const task = await Task.findById(req.params.id);
    if (!task || task.status === 'deleted') {
      return res.status(404).json({ success: false, error: 'Task not found' });
    }

    if (!canUserAccessTask(req.user, task)) {
      return res.status(403).json({ success: false, error: 'Access denied' });
    }

    task.comments.push({
      userId: req.user._id,
      text: text.trim(),
      createdAt: new Date()
    });

    await task.save();
    await notifyCommentAdded(task, req.user._id);

    await task.populate('comments.userId', 'profile.fullName avatar email');

    res.json({
      success: true,
      message: 'Comment added successfully',
      data: task
    });
  } catch (error) {
    console.error('Add comment error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
};

/**
 * @desc    Get overdue tasks
 * @route   GET /api/tasks/overdue
 * @access  Private
 */
const getOverdueTasks = async (req, res) => {
  try {
    const { forTeam = false } = req.query;

    const query = {
      status: { $in: ['todo', 'in_progress'] },
      dueDate: { $lt: new Date() }
    };

    if (!forTeam || req.user.role !== 'team_lead') {
      query.assignedTo = req.user._id;
    } else {
      query.teamId = req.user.teamId;
    }

    const tasks = await Task.find(query)
      .populate('assignedBy assignedTo teamId')
      .sort({ dueDate: 1 });

    res.json({
      success: true,
      count: tasks.length,
      data: tasks.map(t => ({
        ...t.toObject(),
        overdue: true,
        progress: calculateProgress(t)
      }))
    });
  } catch (error) {
    console.error('Get overdue tasks error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

/**
 * @desc    Get task statistics for current user
 * @route   GET /api/tasks/stats
 * @access  Private
 */
const getTaskStats_endpoint = async (req, res) => {
  try {
    const stats = await getTaskStats(req.user._id);

    res.json({
      success: true,
      data: stats
    });
  } catch (error) {
    console.error('Get task stats error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

/**
 * @desc    Add attachment to task
 * @route   POST /api/tasks/:id/attachments
 * @access  Private
 */
const addAttachment = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded'
      });
    }

    const task = await Task.findById(req.params.id);
    if (!task || task.status === 'deleted') {
      deleteFile(req.file.filename);
      return res.status(404).json({
        success: false,
        error: 'Task not found'
      });
    }

    if (!canUserAccessTask(req.user, task)) {
      deleteFile(req.file.filename);
      return res.status(403).json({
        success: false,
        error: 'Not authorized'
      });
    }

    // Add attachment to task
    task.attachments.push({
      name: getOriginalFilename(req.file.filename), // Tên đẹp: "Báo cáo tháng 10.pdf"
      url: req.file.path,
      public_id: req.file.filename,                 // Dùng để xóa sau
      type: req.file.mimetype,
    });

    await task.save();
    await task.populate('comments.userId', 'profile.fullName avatar email'); 

    res.json({
      success: true,
      message: 'File uploaded successfully',
      data: {
        name: req.file.originalname,
        url: getFileUrl(req.file.filename),
        size: req.file.size,
        type: req.file.mimetype
      }
    });
  } catch (error) {
    if (req.file) deleteFile(req.file.filename);
    
    console.error('Add attachment error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

/**
 * @desc    Add multiple attachments to task
 * @route   POST /api/tasks/:id/attachments/bulk
 * @access  Private
 */
const addAttachmentBulk = async (req, res) => {
  try {
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No files uploaded'
      });
    }

    const task = await Task.findById(req.params.id);
    if (!task || task.status === 'deleted') {
      // XÓA TẤT CẢ TRÊN CLOUDINARY
      for (const file of req.files) {
        await deleteFile(file.filename);
      }
      return res.status(404).json({
        success: false,
        error: 'Task not found'
      });
    }

    if (!canUserAccessTask(req.user, task)) {
      for (const file of req.files) {
        await deleteFile(file.filename);
      }
      return res.status(403).json({
        success: false,
        error: 'Not authorized'
      });
    }

    // SỬA LỖI: DÙNG file, KHÔNG PHẢI req.file
    const attachments = req.files.map(file => ({
      name: file.originalname,
      url: file.path,               // URL từ Cloudinary
      public_id: file.filename,     // public_id
      type: file.mimetype
    }));

    task.attachments.push(...attachments);
    await task.save();

    res.json({
      success: true,
      message: 'Files uploaded successfully',
      data: attachments.map((att, index) => ({
        ...att,
        size: req.files[index].size  // DÙNG .bytes, KHÔNG PHẢI .size
      }))
    });
  } catch (error) {
    if (req.files) {
      for (const file of req.files) {
        await deleteFile(file.filename);
      }
    }
    console.error('Add attachment bulk error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

module.exports = {
  createTask,
  getAllTasks,
  getTaskById,
  updateTask,
  deleteTask,
  assignTask,
  updateTaskStatus,
  updateTaskProgress,
  getMyTasks,
  getTeamTasks,
  addComment,
  getOverdueTasks,
  getTaskStats_endpoint,
  addAttachment,
  addAttachmentBulk
};