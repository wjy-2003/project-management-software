from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class TeamMember(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    role = models.CharField(max_length=50, verbose_name="角色")
    join_date = models.DateField(auto_now_add=True, verbose_name="加入日期")

    class Meta:
        verbose_name = "团队成员"
        verbose_name_plural = "团队成员"

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Document(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, verbose_name="文档标题")
    file = models.FileField(upload_to="documents/", verbose_name="文件")
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="上传日期")
    description = models.TextField(blank=True, verbose_name="描述")

    class Meta:
        verbose_name = "文档"
        verbose_name_plural = "文档"

    def __str__(self):
        return self.title


class Task(models.Model):
    # 状态选项
    STATUS_CHOICES = [
        ("not_started", "未开始"),
        ("in_progress", "进行中"),
        ("completed", "已完成"),
        ("suspended", "已暂停"),
    ]

    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="所属项目",
    )
    title = models.CharField(max_length=200, verbose_name="任务标题")
    description = models.TextField(blank=True, verbose_name="任务描述")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_started",
        verbose_name="状态",
    )
    assigned_to = models.ForeignKey(
        TeamMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="指派给",
    )

    # 日期信息
    planned_start_date = models.DateField(
        verbose_name="计划开始日期", null=True, blank=True
    )
    due_date = models.DateField(verbose_name="截止日期", null=True, blank=True)
    actual_start_date = models.DateField(
        verbose_name="实际开始日期", null=True, blank=True
    )
    actual_end_date = models.DateField(
        verbose_name="实际完成日期", null=True, blank=True
    )

    estimated_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="预计工时",
    )
    consumed_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="消耗工时",
    )
    remaining_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        # validators=[MinValueValidator(0)],
        verbose_name="剩余工时",
    )

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务"

    def __str__(self):
        return self.title

    def save(self, *args, force_status=False, **kwargs):
        """重写保存方法，自动计算剩余工时和更新状态

        Args:
            force_status (bool): 是否强制使用当前状态而不自动更新
        """
        # 计算剩余工时
        self.remaining_hours = max(0, self.estimated_hours - self.consumed_hours)

        # 只有在非强制状态时才自动更新状态
        if not force_status:
            if self.consumed_hours == 0:
                self.status = "not_started"
            elif self.consumed_hours > 0 and self.status == "not_started":
                self.status = "in_progress"
            elif self.consumed_hours > 0 and self.status == "suspended":
                self.status = "in_progress"
            # 移除自动将状态设置为"completed"的逻辑，让用户手动完成任务
            # 已完成任务的状态应该由用户通过task_complete视图函数控制

        super().save(*args, **kwargs)

    def get_task_progress(self):
        """计算任务进度"""
        if self.estimated_hours == 0:
            return 0
        progress = (self.consumed_hours / self.estimated_hours) * 100
        return min(100, progress)  # 确保进度不超过100%


class Project(models.Model):
    # 基本信息
    id = models.AutoField(primary_key=True)
    project_number = models.CharField(
        max_length=50, unique=True, verbose_name="项目编号"
    )
    title = models.CharField(max_length=200, verbose_name="项目名称")
    description = models.TextField(blank=True, verbose_name="项目描述")

    # 日期信息
    planned_start_date = models.DateField(verbose_name="计划开始日期")
    planned_end_date = models.DateField(verbose_name="计划完成日期")
    actual_start_date = models.DateField(
        null=True, blank=True, verbose_name="实际开始日期"
    )
    actual_end_date = models.DateField(
        null=True, blank=True, verbose_name="实际完成日期"
    )

    # 工时信息
    estimated_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="预计工时",
    )
    consumed_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="消耗工时",
    )
    remaining_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,  # 添加默认值
        verbose_name="剩余工时",
    )

    # 工作日信息
    available_workdays = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0,  # 添加默认值
        verbose_name="可用工日",
    )
    available_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,  # 添加默认值
        verbose_name="可用工时",
    )

    # 关联信息
    team_members = models.ManyToManyField(
        TeamMember, related_name="projects", blank=True, verbose_name="团队成员"
    )
    documents = models.ManyToManyField(
        Document, related_name="projects", blank=True, verbose_name="文档库"
    )

    # 状态信息
    STATUS_CHOICES = [
        ("planning", "规划中"),
        ("in_progress", "进行中"),
        ("completed", "已完成"),
        ("suspended", "已暂停"),
        ("cancelled", "已取消"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planning",
        verbose_name="项目状态",
    )

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "项目"
        verbose_name_plural = "项目"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project_number} - {self.title}"

    def get_project_progress(self):
        """计算项目进度"""
        if self.estimated_hours == 0:
            return 0
        return (self.consumed_hours / self.estimated_hours) * 100

    def update_project_remaining_hours(self):
        """更新剩余工时"""
        self.remaining_hours = max(0, self.estimated_hours - self.consumed_hours)
        self.save()
