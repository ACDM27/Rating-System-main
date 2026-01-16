# 批量导入用户问题修复

## 问题描述
用户在批量导入观众和评委账号时遇到错误：
```
TypeError: N.value.map is not a function
```

## 问题分析

### 根本原因
后端API返回格式不一致导致前端处理时出错。

**观众批量导入** (`/admin/students/import`)原返回格式：
```json
{
  "message": "成功导入 X 个账号",
  "errors": []
}
```

**评委批量导入** (`/admin/teachers/import`)返回格式：
```json
{
  "created_count": X,
  "errors": [],
  "message": "成功导入 X 个评委，Y 个失败"
}
```

前端代码期望统一的返回格式，当返回格式不一致时会导致错误。

## 解决方案

### 1. 统一后端返回格式
修改观众批量导入API，使其返回格式与评委导入一致：

```python
return {
    "success_count": success_count,
    "created_count": success_count,
    "errors": errors,
    "message": f"成功导入 {success_count} 个账号" + (f"，{len(errors)} 个失败" if errors else "")
}
```

### 2. 确保错误处理
- `errors` 字段始终返回列表（即使为空）
- 添加详细的失败信息
- 成功和失败数量都有明确记录

## 使用方法

### 批量导入观众
1. 下载模板（包含"用户名"和"密码"两列）
2. 填写数据
3. 导入Excel文件
4. 确认预览
5. 点击"确认导入"

### 批量导入评委
1. 下载评委导入模板
2. 填写评委信息
3. 导入Excel
4. 系统会自动：
   - 创建评委账号
   - 关联到当前场次

## Excel模板格式

### 观众模板
| 用户名 | 密码 |
|--------|------|
| audience001 | 123456 |
| audience002 | 123456 |

### 评委模板
| 用户名 | 显示名称 | 密码 |
|--------|----------|------|
| judge001 | 王老师 | 123456 |
| judge002 | 李老师 | 123456 |

## 注意事项
1. 用户名不能重复（系统级唯一）
2. 密码默认为123456
3. 导入成功后会显示成功和失败的数量
4. 重复的用户名会跳过并在errors中报告

## 测试方法
```bash
# 运行数据库检查脚本
cd backend
python check_user_huangkun.py
```

## 已修复
✅ 统一API返回格式
✅ 确保errors字段始终为列表
✅ 添加详细的成功/失败统计
