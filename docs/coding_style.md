# 项目代码风格规范

本项目遵循 [PEP 8](https://peps.python.org/pep-0008/) 及 [Django 官方文档](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/) 推荐的代码风格。

## 1. 缩进与空格
- 使用 4 个空格进行缩进，不使用 Tab。
- 运算符两侧应有一个空格（如 a = b + c），但函数参数列表、索引、切片等不加多余空格。

**示例：**
```python
# 正确
for i in range(10):
    total = i + 1
    print(total)

# 错误（Tab 或无空格）
for i in range(10):
	total=i+1
    print(total)
```

## 2. 行长度
- 每行代码不超过 79 个字符。
- 文档字符串或注释建议不超过 72 个字符。

**示例：**
```python
# 正确
queryset = MyModel.objects.filter(is_active=True)
# 错误（过长）
queryset = MyModel.objects.filter(is_active=True, created__gte=start_date, updated__lte=end_date, status='active')
```

## 3. 空行
- 顶级函数和类定义之间使用两个空行。
- 类内方法之间使用一个空行。

**示例：**
```python
# 正确

def foo():
    pass

class Bar:
    def method_one(self):
        pass

    def method_two(self):
        pass
```

## 4. 导入规范
- 每个导入语句单独一行。
- 导入顺序：标准库、第三方库、本地应用。
- 使用绝对导入，Django app 内可用相对导入。

**示例：**
```python
# 正确
import os
import django
from myapp.models import MyModel

# 错误
import os, django
from .models import MyModel  # 仅限 app 内部
```

## 5. 命名规范
- 变量、函数、方法使用小写字母+下划线（snake_case）。
- 类名使用大驼峰（CapWords）。
- 常量全大写+下划线。

**示例：**
```python
# 正确
user_name = 'Tom'
def get_user():
    pass

class UserProfile:
    pass

MAX_SIZE = 100
```

## 6. 文档字符串与注释
- 所有公开模块、函数、类、方法应有文档字符串（docstring）。
- 注释应简洁明了，避免无意义注释。

**示例：**
```python
# 正确
def add(a, b):
    """返回两个数的和"""
    return a + b

# 错误
# 这是加法函数
def add(a, b):
    return a + b
```

## 7. Django 特有建议
- Model、View、Form、Template 命名应清晰表达用途。
- 尽量使用 Django 内置功能（如 QuerySet API、Form 验证等），避免重复造轮子。
- 配置文件（如 settings.py）分组清晰，注释说明特殊配置。
- URL 路由命名应简洁，避免重复。
- 使用 `get_object_or_404`、`get_list_or_404` 等快捷方法处理对象获取。

**示例：**
```python
# models.py
class Project(models.Model):
    name = models.CharField(max_length=100)

# views.py
from django.shortcuts import get_object_or_404

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    ...

# urls.py
urlpatterns = [
    path('project/<int:pk>/', project_detail, name='project_detail'),
]
```

## 8. 其他建议
- 遵循 DRY（Don't Repeat Yourself）原则。
- 代码提交前请运行 flake8/pylint 检查。
- 推荐使用 Black 或 isort 工具自动格式化代码。

**示例：**
```python
# DRY 原则
# 错误
if status == 'active':
    do_something()
if status == 'active':
    do_another()

# 正确
def handle_active():
    if status == 'active':
        do_something()
        do_another()
```

---
如需详细规范请参考 PEP 8 与 Django 官方文档。

---

# Project Code Style Guide (English)

This project follows [PEP 8](https://peps.python.org/pep-0008/) and [Django Official Documentation](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/) recommended coding styles.

## 1. Indentation & Spaces
- Use 4 spaces for indentation, do not use tabs.
- Add one space around operators (e.g., a = b + c), but do not add extra spaces in function parameter lists, indexing, or slicing.

**Example:**
```python
# Correct
for i in range(10):
    total = i + 1
    print(total)

# Incorrect (Tab or no spaces)
for i in range(10):
	total=i+1
    print(total)
```

## 2. Line Length
- Limit all lines to a maximum of 79 characters.
- Docstrings and comments are recommended to be no more than 72 characters.

**Example:**
```python
# Correct
queryset = MyModel.objects.filter(is_active=True)
# Incorrect (too long)
queryset = MyModel.objects.filter(is_active=True, created__gte=start_date, updated__lte=end_date, status='active')
```

## 3. Blank Lines
- Use two blank lines between top-level functions and class definitions.
- Use one blank line between methods within a class.

**Example:**
```python
# Correct

def foo():
    pass

class Bar:
    def method_one(self):
        pass

    def method_two(self):
        pass
```

## 4. Import Conventions
- Each import statement should be on its own line.
- Import order: standard library, third-party libraries, local apps.
- Use absolute imports; relative imports are allowed within Django apps.

**Example:**
```python
# Correct
import os
import django
from myapp.models import MyModel

# Incorrect
import os, django
from .models import MyModel  # Only for app internal
```

## 5. Naming Conventions
- Use snake_case for variables, functions, and methods.
- Use CapWords for class names.
- Use ALL_CAPS for constants.

**Example:**
```python
# Correct
user_name = 'Tom'
def get_user():
    pass

class UserProfile:
    pass

MAX_SIZE = 100
```

## 6. Docstrings & Comments
- All public modules, functions, classes, and methods should have docstrings.
- Comments should be concise and meaningful; avoid unnecessary comments.

**Example:**
```python
# Correct
def add(a, b):
    """Return the sum of two numbers."""
    return a + b

# Incorrect
# This is an add function
def add(a, b):
    return a + b
```

## 7. Django Specific Suggestions
- Name Models, Views, Forms, and Templates to clearly express their purpose.
- Prefer Django built-in features (e.g., QuerySet API, Form validation) over reinventing the wheel.
- Group settings in configuration files (e.g., settings.py) clearly, and comment on special configurations.
- Name URL routes concisely and avoid duplication.
- Use `get_object_or_404`, `get_list_or_404` for object retrieval shortcuts.

**Example:**
```python
# models.py
class Project(models.Model):
    name = models.CharField(max_length=100)

# views.py
from django.shortcuts import get_object_or_404

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    ...

# urls.py
urlpatterns = [
    path('project/<int:pk>/', project_detail, name='project_detail'),
]
```

## 8. Other Suggestions
- Follow the DRY (Don't Repeat Yourself) principle.
- Run flake8/pylint before code submission.
- Use Black or isort for automatic code formatting.

**Example:**
```python
# DRY principle
# Incorrect
if status == 'active':
    do_something()
if status == 'active':
    do_another()

# Correct
def handle_active():
    if status == 'active':
        do_something()
        do_another()
```

---
For more details, please refer to PEP 8 and Django Official Documentation.
