const multer = require('multer');
const { v2: cloudinary } = require('cloudinary');
const { CloudinaryStorage } = require('multer-storage-cloudinary');

// === DANH SÁCH ĐUÔI FILE BỊ CẤM (MÃ ĐỘC, MACRO, EXECUTABLE...) ===
const BLOCKED_EXTENSIONS = [
  'exe', 'scr', 'com', 'bat', 'cmd', 'ps1', 'vbs', 'vbe', 'js', 'jse',
  'wsf', 'wsh', 'msc', 'msp', 'mst', 'pif', 'application', 'gadget',
  'hta', 'lnk', 'inf', 'reg', 'cpl', 'sh', 'bash', 'zsh', 'ksh', 'csh',
  'apk', 'deb', 'rpm', 'app', 'run', 'command',
  'dll', 'so', 'dylib', 'jar', 'class',
  'docm', 'dotm', 'xlsm', 'xltm', 'xlam', 'pptm', 'potm', 'ppam', 'sldm',
  'iso', 'img', 'dmg', 'msi', 'msp', 'msu', 'cab', 'swf', 'air'
];

const isExtensionBlocked = (filename) => {
  if (!filename) return false;
  const ext = filename.toLowerCase().split('.').pop();
  return BLOCKED_EXTENSIONS.includes(ext);
};

// === TẠO TÊN FILE DUY NHẤT NHƯNG GIỮ NGUYÊN TÊN GỐC ĐỂ HIỂN THỊ ===
const generateUniquePublicId = (originalname, userId) => {
  const ext = originalname.split('.').pop();
  const originalWithoutExt = originalname.slice(0, -(ext.length + 1)).trim();

  // Tạo prefix duy nhất để tránh trùng
  const uniquePrefix = `${userId}-${Date.now()}-${Math.round(Math.random() * 1E9)}`;

  // Kết quả: user123-1735928340000-987654321--Báo cáo tháng 10.pdf
  return `${uniquePrefix}--${originalWithoutExt}`;
};

// === LẤY LẠI TÊN GỐC ĐỂ LƯU VÀO DATABASE ===
const getOriginalFilename = (publicId) => {
  if (!publicId) return 'unknown-file';
  const parts = publicId.split('--');
  if (parts.length >= 2) {
    const rest = parts.slice(1).join('--');
    const lastDotIndex = rest.lastIndexOf('.');
    if (lastDotIndex > 0) {
      return rest;
    }
  }
  return publicId + '.file'; // fallback
};

// Cấu hình Cloudinary
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

// === STORAGE: KHÔNG DÙNG allowed_formats → TRÁNH LỖI ===
const storage = new CloudinaryStorage({
  cloudinary,
  params: (req, file) => {
    if (isExtensionBlocked(file.originalname)) {
      throw new Error(`File bị chặn vì lý do bảo mật: .${file.originalname.split('.').pop()}`);
    }

    const publicId = generateUniquePublicId(file.originalname, req.user._id);

    return {
      folder: 'tma-tasks',
      resource_type: 'auto',
      public_id: publicId,
    };
  },
});

// === FILE FILTER: CHẶN TRƯỚC KHI UPLOAD ===
const fileFilter = (req, file, cb) => {
  if (isExtensionBlocked(file.originalname)) {
    return cb(new Error(`Không được phép upload file có đuôi ".${file.originalname.split('.').pop()}" vì lý do bảo mật`), false);
  }

  const allowedMimes = [
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain', 'text/csv',
    'application/zip', 'application/x-zip-compressed',
    'application/vnd.rar'
  ];

  if (!allowedMimes.includes(file.mimetype)) {
    return cb(new Error('Only allowed PDF, Word, Excel, PowerPoint, TXT, CSV, ZIP'), false);
  }

  cb(null, true);
};

// === MULTER INSTANCE ===
const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB
  },
});

const uploadSingle = upload.single('attachment');
const uploadMultiple = upload.array('attachments', 5);

// === XỬ LÝ LỖI ĐẸP ===
const uploadErrorHandler = (err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ success: false, error: 'File quá lớn. Tối đa 10MB' });
    }
    if (err.code === 'LIMIT_FILE_COUNT') {
      return res.status(400).json({ success: false, error: 'Tối đa 5 file mỗi lần upload' });
    }
  }

  if (err) {
    return res.status(400).json({
      success: false,
      error: err.message || 'Upload thất bại'
    });
  }

  next();
};

// === HELPER: LẤY TÊN GỐC ĐỂ LƯU DATABASE ===
const getFileUrl = (file) => file.path;


// === XÓA FILE ===
const deleteFile = async (publicId) => {
  try {
    if (!publicId) return false;
    const result = await cloudinary.uploader.destroy(publicId);
    return result.result === 'ok';
  } catch (error) {
    console.error('Cloudinary delete error:', error);
    return false;
  }
};

// === EXPORT ===
module.exports = {
  uploadSingle,
  uploadMultiple,
  uploadErrorHandler,
  getFileUrl,
  deleteFile,
  cloudinary,
  getOriginalFilename, // DÙNG TRONG CONTROLLER ĐỂ LƯU TÊN ĐẸP
};