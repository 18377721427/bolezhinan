# -*- coding: utf-8 -*-
"""伯乐职南 · 数据库模型定义"""
import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def today():
    return datetime.date.today().strftime('%Y-%m-%d')

# ─── 用户 ───
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(80), default='管理员')
    role = db.Column(db.String(20), default='admin')  # admin / operator
    created_at = db.Column(db.String(20), default=now)

    def to_dict(self):
        return {'id': self.id, 'username': self.username,
                'display_name': self.display_name, 'role': self.role}

# ─── 活动 ───
ACTIVITY_STATUS = ('draft', 'published', 'ongoing', 'ended')

class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    theme = db.Column(db.String(200), default='')
    date = db.Column(db.String(20), default='')
    time = db.Column(db.String(20), default='')
    venue = db.Column(db.String(200), default='')
    guest_desc = db.Column(db.Text, default='')
    ticket_price = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='draft')
    based_on_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    version = db.Column(db.Integer, default=1)
    max_participants = db.Column(db.Integer, default=30)
    desc_text = db.Column(db.Text, default='')
    highlight_text = db.Column(db.Text, default='')
    tags = db.Column(db.String(200), default='')
    flow_json = db.Column(db.Text, default='[]')  # JSON 活动流程
    created_at = db.Column(db.String(20), default=now)
    updated_at = db.Column(db.String(20), default=now)
    deleted_at = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        d.pop('password_hash', None)
        return d

class ActivityVersion(db.Model):
    __tablename__ = 'activity_versions'
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    snapshot_json = db.Column(db.Text, nullable=False)
    version = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.String(80), default='admin')
    created_at = db.Column(db.String(20), default=now)

# ─── 任务 ───
TASK_PHASES = ('策划期', '准备期', '推广期', '执行期', '收尾期', '复盘期')
TASK_STATUS = ('todo', 'in_progress', 'done', 'overdue')

class TaskTemplate(db.Model):
    __tablename__ = 'task_templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phase = db.Column(db.String(20), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    days_before = db.Column(db.Integer, default=7)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    phase = db.Column(db.String(20), nullable=False)
    assignee = db.Column(db.String(80), default='')
    due_date = db.Column(db.String(20), default='')
    status = db.Column(db.String(20), default='todo')
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.String(20), default=now)
    updated_at = db.Column(db.String(20), default=now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# ─── 报名 ───
class Registration(db.Model):
    __tablename__ = 'registrations'
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    wechat = db.Column(db.String(80), default='')
    source_channel = db.Column(db.String(20), default='')
    payment_status = db.Column(db.String(20), default='unpaid')
    checkin_status = db.Column(db.String(20), default='unchecked')
    created_at = db.Column(db.String(20), default=now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# ─── 客户 ───
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), default='')
    wechat = db.Column(db.String(80), default='')
    source_channel = db.Column(db.String(20), default='')
    total_participations = db.Column(db.Integer, default=1)
    first_activity_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.String(20), default=now)
    updated_at = db.Column(db.String(20), default=now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# ─── 模板（简化版） ───
class Template(db.Model):
    __tablename__ = 'templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), default='')  # 海报文案/邀约话术/签到表/文档
    content = db.Column(db.Text, default='')
    current_version = db.Column(db.Integer, default=1)
    linked_activity_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.String(20), default=now)
    updated_at = db.Column(db.String(20), default=now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class TemplateVersion(db.Model):
    __tablename__ = 'template_versions'
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    content_snapshot = db.Column(db.Text, default='')
    version = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.String(80), default='admin')
    created_at = db.Column(db.String(20), default=now)

# ─── 操作日志 ───
class OperationLog(db.Model):
    __tablename__ = 'operation_logs'
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(50), default='')
    action = db.Column(db.String(100), default='')
    operator = db.Column(db.String(80), default='')
    detail = db.Column(db.Text, default='')
    created_at = db.Column(db.String(20), default=now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# ─── 反馈 ───
class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    customer_name = db.Column(db.String(80), default='')
    raw_text = db.Column(db.Text, default='')  # 原话
    category = db.Column(db.String(20), default='')  # 优点/待提高/想了解
    created_at = db.Column(db.String(20), default=now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# ─── 站点配置 ───
class SiteConfig(db.Model):
    __tablename__ = 'site_config'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, default='')
    updated_at = db.Column(db.String(20), default=now)
