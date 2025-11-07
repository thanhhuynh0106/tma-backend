const User = require('../models/User');
const Attendance = require('../models/Attendance');


/**
 * Calculate work hours between clock-in and clock-out
 * @param {Date} clockIn
 * @param {Date} clockOut
 * @returns {Number}
**/
const calculateWorkHours = (clockIn, clockOut) => {
    const inTime = new Date(clockIn);
    const outTime = new Date(clockOut);
    const diffMs = outTime - inTime;
    const diffHrs = diffMs / (1000 * 60 * 60);
    return parseFloat(diffHrs.toFixed(2));
}


/**
 * Determine attendance status based on clock-in time (late or not)
 * @param {Date} clockInTime
 * @returns {String}
**/ 
const determineStatus = (clockInTime) => {
    const inTime = new Date(clockInTime);
    const standardStart = new Date(inTime);
    standardStart.setHours(9, 0, 0, 0); // 9:00 AM
    return inTime <= standardStart ? 'on_time' : 'late';    
}


/** 
 * Get today's attendance record for a user
 * @param {String} userId
 * @returns {Object|null}
**/
const getTodayAttendance = async (userId) => {
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date();
    endOfDay.setHours(23, 59, 59, 999);
    return await Attendance.findOne({
        userId,
        date: { $gte: startOfDay, $lte: endOfDay }
    });
}


/**
 * Get attendance statistics for a user over a date range
 * @param {String} userId
 * @param {Date} startDate
 * @param {Date} endDate
 * @returns {Object}
 */
const getAttendanceStats = async (userId, startDate, endDate) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const records = await Attendance.find({
        userId,
        date: { $gte: start, $lte: end }
    });

    const totalDays = records.length;
    const presentDays = records.filter(r => r.status === 'present').length;
    const lateDays = records.filter(r => r.status === 'late').length;
    const absentDays = records.filter(r => r.status === 'absent').length;

    return {
        totalDays,
        presentDays,
        lateDays,
        absentDays
    };
}


/**
 * Validate if location is within allowed area
 * @param {Number} lat
 * @param {Number} lng
 * @returns {Boolean}
 **/
const validateLocation = (lat, lng) => {
    // 10.871556, 106.803221 // cb
    // 10.869093, 106.803103 // cn
    // 10.869935, 106.805138 // cd
    // 10.869913, 106.802012 // ct
    const allowedArea = {
        latMin: 10.869093,
        latMax: 10.871556,
        lngMin: 106.802012,
        lngMax: 106.805138
    };

    return lat >= allowedArea.latMin && lat <= allowedArea.latMax &&
           lng >= allowedArea.lngMin && lng <= allowedArea.lngMax;
}

module.exports = {
    calculateWorkHours,
    determineStatus,
    getTodayAttendance,
    getAttendanceStats,
    validateLocation
};