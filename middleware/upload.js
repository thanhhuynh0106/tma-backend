// === middleware/upload.js === (ĐÃ SỬA HOÀN CHỈNH)
const multer = require('multer');
const { v2: cloudinary } = require('cloudinary');
const { CloudinaryStorage } = require('multer-storage-cloudinary');

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

// Tạo public_id an toàn (không chứa tiếng Việt)
const generateSafePublicId = (originalname, userId) => {
  const ext = originalname.split('.').pop() || 'file';
  const timestamp = Date.now();
  const random = Math.round(Math.random() * 1E9);
  return `tma-tasks/${userId}-${timestamp}-${random}.${ext}`;
};

// QUAN TRỌNG: Fix lỗi split is not a function
const getOriginalFilename = (fileOrPublicId) => {
  if (!fileOrPublicId) return 'unknown-file';

  // Nếu là file từ multer (có originalname)
  if (typeof fileOrPublicId === 'object' && fileOrPublicId.originalname) {
    return fileOrPublicId.originalname.trim();
  }

  // Nếu chỉ là public_id string (trường hợp cũ)
  if (typeof fileOrPublicId === 'string') {
    const parts = fileOrPublicId.split('--');
    if (parts.length >= 2) {
      return parts.slice(1).join('--').trim();
    }
    // Fallback: lấy tên từ URL hoặc public_id
    const match = fileOrPublicId.match(/[^/]+\.[a-zA-Z0-9]+$/);
    return match ? decodeURIComponent(match[0]) : 'file';
  }

  return 'unknown-file';
};

cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

const storage = new CloudinaryStorage({
  cloudinary,
  params: (req, file) => {
    if (isExtensionBlocked(file.originalname)) {
      throw new Error(`File bị chặn: .${file.originalname.split('.').pop()}`);
    }

    return {
      folder: 'tma-tasks',
      resource_type: 'auto',
      public_id: generateSafePublicId(file.originalname, req.user._id),
      use_filename: true,
      unique_filename: false,
      overwrite: false,
    };
  },
});

const fileFilter = (req, file, cb) => {
  if (isExtensionBlocked(file.originalname)) {
    return cb(new Error(`Không cho phép file .${file.originalname.split('.').pop()}`), false);
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
    'text/plain', 'text/csv', 'application/csv', 'text/comma-separated-values',
    'application/zip', 'application/x-zip-compressed',
    'application/vnd.rar', 'application/x-rar-compressed',
    'application/octet-stream'
  ];
  if (!allowedMimes.includes(file.mimetype)) {
    return cb(new Error('Chỉ chấp nhận ảnh, PDF, Office, ZIP, RAR'), false);
  }
  cb(null, true);
};

const upload = multer({
  storage,
  fileFilter,
  limits: { fileSize: 10 * 1024 * 1024 },
});

const uploadSingle = upload.single('attachment');
const uploadMultiple = upload.array('attachments', 5);

const uploadErrorHandler = (err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') return res.status(400).json({ success: false, error: 'File quá lớn (tối đa 10MB)' });
    if (err.code === 'LIMIT_FILE_COUNT') return res.status(400).json({ success: false, error: 'Tối đa 5 file' });
  }
  if (err) return res.status(400).json({ success: false, error: err.message || 'Upload thất bại' });
  next();
};

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

module.exports = {
  uploadSingle,
  uploadMultiple,
  uploadErrorHandler,
  deleteFile,
  getOriginalFilename,
  cloudinary,
};