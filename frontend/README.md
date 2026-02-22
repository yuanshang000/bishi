# 大学英语智慧助手 - 前端项目

## 项目简介

基于Vue 3 + TypeScript + Element Plus开发的大学英语学习辅助系统前端应用，对接完整的后端API。

## 技术栈

### 核心框架
- **Vue 3.4.0** - 渐进式JavaScript框架
- **TypeScript 5.3.0** - 类型安全
- **Vite 5.0.0** - 下一代前端构建工具

### UI组件库
- **Element Plus 2.5.0** - Vue 3 UI组件库
- **@element-plus/icons-vue 2.3.1** - Element Plus图标

### 状态管理与路由
- **Pinia 2.1.7** - Vue 3状态管理
- **Vue Router 4.2.5** - 路由管理

### HTTP客户端
- **Axios 1.6.2** - Promise based HTTP客户端

### 其他
- **marked 11.1.0** - Markdown解析
- **dayjs 1.11.10** - 日期处理

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API接口层
│   │   ├── auth.ts       # 认证接口
│   │   ├── chapters.ts   # 章节接口
│   │   ├── documents.ts  # 文档接口
│   │   ├── quiz.ts       # 练习接口
│   │   ├── chat.ts       # 聊天接口
│   │   └── index.ts      # 统一导出
│   ├── stores/           # Pinia状态管理
│   │   ├── user.ts       # 用户状态
│   │   ├── chapter.ts    # 章节状态
│   │   └── index.ts      # 统一导出
│   ├── router/           # 路由配置
│   │   └── index.ts      # 路由定义
│   ├── views/            # 页面组件
│   │   ├── Login.vue     # 登录注册页
│   │   ├── Home.vue      # 首页
│   │   ├── Chapters.vue  # 章节管理
│   │   ├── Documents.vue # 文档管理
│   │   ├── Quiz.vue      # 练习中心
│   │   └── Chat.vue      # 智能问答
│   ├── layout/           # 布局组件
│   │   └── MainLayout.vue # 主布局
│   ├── types/            # TypeScript类型定义
│   │   └── index.ts      # 类型定义
│   ├── utils/            # 工具函数
│   │   └── request.ts    # Axios封装
│   ├── App.vue           # 根组件
│   └── main.ts           # 应用入口
├── index.html            # HTML模板
├── vite.config.ts        # Vite配置
├── tsconfig.json         # TypeScript配置
├── package.json          # 项目依赖
└── start.bat             # 启动脚本(Windows)
```

## 功能特性

### ✅ 已实现功能

#### 1. 用户认证
- ✅ 用户注册（支持学生/教师角色）
- ✅ 用户登录
- ✅ JWT令牌管理
- ✅ 自动token刷新
- ✅ 退出登录

#### 2. 首页看板
- ✅ 章节统计
- ✅ 文档统计
- ✅ 练习统计
- ✅ 最近练习记录
- ✅ 快速操作入口

#### 3. 章节管理（教师）
- ✅ 章节列表展示
- ✅ 创建章节
- ✅ 编辑章节
- ✅ 删除章节
- ✅ 章节详情

#### 4. 文档管理（教师）
- ✅ 文档列表展示
- ✅ 按章节过滤
- ✅ 文件上传（PDF/DOCX/TXT）
- ✅ 文档向量化
- ✅ 删除文档
- ✅ 向量化状态显示

#### 5. 练习中心
- ✅ 选择章节和题型
- ✅ 自定义题目数量
- ✅ AI生成练习题
- ✅ 在线答题
- ✅ 自动计时
- ✅ 提交答案
- ✅ 成绩统计
- ✅ 练习历史记录

#### 6. 智能问答
- ✅ 实时聊天对话
- ✅ RAG增强回答
- ✅ 按章节检索
- ✅ 会话管理
- ✅ 消息历史
- ✅ 新会话创建

#### 7. 权限控制
- ✅ 基于角色的路由守卫
- ✅ 教师/学生权限区分
- ✅ 菜单动态显示

## API对接情况

### 全部27个API接口已对接 ✅

#### 认证API (5个) ✅
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新令牌
- `GET /api/v1/auth/me` - 获取当前用户
- `GET /api/v1/auth/users/{id}` - 获取用户信息

#### 章节API (5个) ✅
- `GET /api/v1/chapters/` - 获取章节列表
- `GET /api/v1/chapters/{id}` - 获取章节详情
- `POST /api/v1/chapters/` - 创建章节
- `PUT /api/v1/chapters/{id}` - 更新章节
- `DELETE /api/v1/chapters/{id}` - 删除章节

#### 文档API (6个) ✅
- `GET /api/v1/documents/` - 获取文档列表
- `GET /api/v1/documents/{id}` - 获取文档详情
- `POST /api/v1/documents/` - 创建文档
- `POST /api/v1/documents/upload` - 上传文档
- `POST /api/v1/documents/{id}/vectorize` - 向量化文档
- `DELETE /api/v1/documents/{id}` - 删除文档

#### 练习API (5个) ✅
- `POST /api/v1/quiz/create` - 创建练习
- `POST /api/v1/quiz/submit` - 提交答案
- `GET /api/v1/quiz/history` - 获取历史
- `GET /api/v1/quiz/stats` - 获取统计
- `GET /api/v1/quiz/{id}` - 获取详情

#### 聊天API (4个) ✅
- `POST /api/v1/chat/` - 发送消息
- `GET /api/v1/chat/history/{id}` - 获取历史
- `GET /api/v1/chat/sessions` - 获取会话列表
- `DELETE /api/v1/chat/session/{id}` - 删除会话

#### 系统API (2个) ✅
- `GET /health` - 健康检查
- `GET /` - 根路径

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

**Windows:**
```bash
.\start.bat
```

**Linux/Mac:**
```bash
npm run dev
```

### 3. 访问应用

打开浏览器访问: http://localhost:5173

## 测试流程

### 完整黑盒测试步骤

#### 1. 用户注册与登录
1. 访问 http://localhost:5173
2. 点击"没有账号？立即注册"
3. 填写注册信息：
   - 用户名：teacher1
   - 密码：password123
   - 角色：教师
4. 注册成功后，使用相同账号登录

#### 2. 章节管理测试（教师）
1. 点击左侧"章节管理"菜单
2. 点击"新建章节"按钮
3. 填写章节信息：
   - 章节编号：1
   - 标题：Unit 1: Campus Life
   - 描述：Introduction to campus life
   - 难度：intermediate
4. 提交创建
5. 测试编辑和删除功能

#### 3. 文档管理测试（教师）
1. 点击"文档管理"菜单
2. 点击"上传文档"按钮
3. 选择章节、输入标题、选择文件类型
4. 上传PDF/DOCX/TXT文件
5. 等待上传完成
6. 点击"向量化"按钮
7. 等待向量化完成
8. 查看向量化状态变为"已向量化"

#### 4. 练习测试
1. 点击"练习中心"菜单
2. 选择章节
3. 选择题型（选择题/填空题/翻译题）
4. 设置题目数量
5. 点击"开始练习"
6. 等待AI生成题目
7. 完成答题
8. 提交答案
9. 查看成绩和解析
10. 查看练习历史记录

#### 5. 智能问答测试
1. 点击"智能问答"菜单
2. （可选）选择相关章节
3. 输入问题，例如：
   - "What is the main topic of Unit 1?"
   - "Explain the grammar rules in this chapter"
4. 点击"发送"或按Ctrl+Enter
5. 等待AI回复
6. 继续多轮对话
7. 测试新建会话功能

#### 6. 数据统计查看
1. 返回"首页"
2. 查看各项统计数据
3. 查看最近练习记录
4. 使用快速操作按钮

## 注意事项

### 前端配置

1. **代理配置**: vite.config.ts中已配置API代理到后端
   ```typescript
   proxy: {
     '/api': {
       target: 'http://localhost:8000',
       changeOrigin: true
     }
   }
   ```

2. **Token管理**: 使用localStorage存储JWT token

### 后端依赖

确保后端服务已启动：
```bash
cd ../backend
.\start.bat
```

后端应运行在: http://localhost:8000

## 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录

## 预览生产版本

```bash
npm run preview
```

## 开发提示

### 调试技巧

1. **API调试**: 打开浏览器开发者工具的Network标签
2. **状态调试**: 安装Vue Devtools浏览器扩展
3. **错误查看**: 查看Console标签的错误信息

### 常见问题

1. **CORS错误**: 确保后端已配置CORS允许前端域名
2. **401未授权**: Token可能已过期，重新登录
3. **连接失败**: 检查后端服务是否正常运行

## 项目特色

1. **完整的类型系统**: 使用TypeScript提供完整类型定义
2. **统一的错误处理**: Axios拦截器统一处理错误
3. **响应式设计**: Element Plus组件库提供良好的UI体验
4. **状态持久化**: 用户登录状态自动保存
5. **路由守卫**: 自动跳转未登录用户到登录页

---

**开发完成！** 🎉

所有功能已实现，可以开始黑盒测试。
