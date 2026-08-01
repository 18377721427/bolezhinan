# -*- coding: utf-8 -*-
"""伯乐职南 · 飞书多维表格集成模块（纯 Python 标准库，无需 lark-cli）"""
import requests
import json
import time


# ─── 自定义异常 ───

class FeishuCliError(Exception):
    """飞书 API 调用异常"""
    pass


class FeishuApiError(Exception):
    """飞书 API 返回错误"""
    def __init__(self, error_obj):
        self.error_obj = error_obj
        msg = error_obj.get('message', '未知错误')
        super().__init__(msg)


# ─── 表格 Schema 定义 ───

ACTIVITIES_SCHEMA = {
    'key': 'activities',
    'name': '活动管理',
    'fields': [
        {'name': '活动名称', 'type': 'text'},
        {'name': '活动主题', 'type': 'text'},
        {'name': '活动日期', 'type': 'datetime'},
        {'name': '活动时间', 'type': 'text'},
        {'name': '场地', 'type': 'text'},
        {'name': '嘉宾介绍', 'type': 'text'},
        {'name': '票价', 'type': 'number'},
        {'name': '状态', 'type': 'select', 'multiple': False,
         'options': [{'name': 'draft'}, {'name': 'published'}, {'name': 'ongoing'}, {'name': 'ended'}]},
        {'name': '最大人数', 'type': 'number'},
        {'name': '活动描述', 'type': 'text'},
        {'name': '亮点', 'type': 'text'},
        {'name': '标签', 'type': 'text'},
    ]
}

REGISTRATIONS_SCHEMA = {
    'key': 'registrations',
    'name': '报名记录',
    'fields': [
        {'name': '姓名', 'type': 'text'},
        {'name': '手机号', 'type': 'text'},
        {'name': '微信号', 'type': 'text'},
        {'name': '来源渠道', 'type': 'text'},
        {'name': '付款状态', 'type': 'select', 'multiple': False,
         'options': [{'name': 'unpaid'}, {'name': 'paid'}]},
        {'name': '签到状态', 'type': 'select', 'multiple': False,
         'options': [{'name': 'unchecked'}, {'name': 'checked'}]},
        {'name': '报名时间', 'type': 'datetime'},
        {'name': '活动ID', 'type': 'number'},
    ]
}

CUSTOMERS_SCHEMA = {
    'key': 'customers',
    'name': '客户信息',
    'fields': [
        {'name': '姓名', 'type': 'text'},
        {'name': '手机号', 'type': 'text'},
        {'name': '微信号', 'type': 'text'},
        {'name': '来源渠道', 'type': 'text'},
        {'name': '累计参与', 'type': 'number'},
        {'name': '创建时间', 'type': 'datetime'},
    ]
}

ALL_SCHEMAS = [ACTIVITIES_SCHEMA, REGISTRATIONS_SCHEMA, CUSTOMERS_SCHEMA]


class FeishuBaseClient:
    """飞书多维表格客户端（通过 HTTP API 调用）"""

    def __init__(self, base_token=None, tenant_token=None):
        self.base_token = base_token
        self.tenant_token = tenant_token
        self._api_base = "https://open.feishu.cn/open-apis/bitable/v1"
        self._auth_base = "https://open.feishu.cn/open-apis/auth/v3"

    def _headers(self):
        if not self.tenant_token:
            raise FeishuCliError('未配置飞书 tenant access token')
        return {
            'Authorization': f'Bearer {self.tenant_token}',
            'Content-Type': 'application/json',
        }

    def _request(self, method, path, **kwargs):
        url = f"{self._api_base}{path}"
        headers = self._headers()
        timeout = kwargs.pop('timeout', 30)
        try:
            resp = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)
            data = resp.json()
            if data.get('code') != 0:
                raise FeishuApiError({'message': data.get('msg', '未知错误')})
            return data.get('data', {})
        except requests.RequestException as e:
            raise FeishuCliError(f'飞书 API 请求失败: {e}')

    def check_cli(self):
        return bool(self.tenant_token)

    def resolve_base(self, url):
        raise FeishuApiError({'message': '请在前端配置页面手动填入 base_token'})

    def list_tables(self):
        if not self.base_token:
            raise FeishuCliError('未配置飞书 base_token')
        data = self._request('GET', f'/apps/{self.base_token}/tables', params={'page_size': 100})
        items = data.get('items', [])
        return items if items else data.get('has_more', False) and items or []

    def table_exists(self, table_name):
        tables = self.list_tables()
        for t in tables:
            if t.get('name') == table_name:
                return t.get('table_id')
        return None

    def create_table(self, name, fields_schema):
        if not self.base_token:
            raise FeishuCliError('未配置飞书 base_token')
        body = {
            'table': {
                'name': name,
                'fields': [
                    {'field_name': f.get('name'), 'type': self._map_type(f.get('type', 1))}
                    for f in fields_schema
                ]
            }
        }
        data = self._request('POST', f'/apps/{self.base_token}/tables', json=body)
        table = data.get('table', data)
        return table.get('table_id'), table.get('name')

    @staticmethod
    def _map_type(t):
        mapping = {'text': 1, 'number': 2, 'select': 3, 'datetime': 5, 'checkbox': 7}
        return mapping.get(t, 1)

    def create_missing_fields(self, table_id, fields_schema):
        return []

    def batch_create_records(self, table_id, records, batch_size=200):
        if not records:
            return {'ok': True, 'total': 0, 'batches': 0}
        total = 0
        batches = 0
        for i in range(0, len(records), batch_size):
            chunk = records[i:i + batch_size]
            body = {
                'records': [
                    {'fields': self._map_record(r)} for r in chunk
                ]
            }
            self._request('POST', f'/apps/{self.base_token}/tables/{table_id}/records/batch_create', json=body)
            total += len(chunk)
            batches += 1
            if i + batch_size < len(records):
                time.sleep(0.5)
        return {'ok': True, 'total': total, 'batches': batches}

    @staticmethod
    def _map_record(record):
        return {k: v for k, v in record.items() if v is not None and v != ''}

    def list_records(self, table_id, limit=200):
        all_records = []
        page_token = None
        while True:
            params = {'page_size': limit}
            if page_token:
                params['page_token'] = page_token
            data = self._request('GET', f'/apps/{self.base_token}/tables/{table_id}/records', params=params)
            items = data.get('items', [])
            all_records.extend(items)
            if not data.get('has_more') or not data.get('page_token'):
                break
            page_token = data.get('page_token')
        return all_records

    def ensure_tables(self, base_token=None):
        if base_token:
            self.base_token = base_token
        if not self.base_token:
            raise FeishuCliError('未配置 base_token')
        result = {}
        for schema in ALL_SCHEMAS:
            key = schema['key']
            name = schema['name']
            existing_id = self.table_exists(name)
            if existing_id:
                result[key] = existing_id
            else:
                tid, _ = self.create_table(name, schema['fields'])
                if tid:
                    result[key] = tid
        return result

    def sync_activities(self, table_id, activities_data):
        if not activities_data:
            return {'ok': True, 'total': 0, 'batches': 0}
        records = []
        for act in activities_data:
            records.append({
                '活动名称': act.get('name', ''),
                '活动主题': act.get('theme', '') or '',
                '活动日期': act.get('date', '') or '',
                '活动时间': act.get('time', '') or '',
                '场地': act.get('venue', '') or '',
                '嘉宾介绍': act.get('guest_desc', '') or '',
                '票价': act.get('ticket_price', 0),
                '状态': act.get('status', 'draft'),
                '最大人数': act.get('max_participants', 0),
                '活动描述': act.get('desc_text', '') or '',
                '亮点': act.get('highlight_text', '') or '',
                '标签': act.get('tags', '') or '',
            })
        return self.batch_create_records(table_id, records)

    def sync_registrations(self, table_id, registrations_data):
        if not registrations_data:
            return {'ok': True, 'total': 0, 'batches': 0}
        records = []
        for reg in registrations_data:
            records.append({
                '姓名': reg.get('name', ''),
                '手机号': reg.get('phone', '') or '',
                '微信号': reg.get('wechat', '') or '',
                '来源渠道': reg.get('source_channel', '') or '',
                '付款状态': reg.get('payment_status', 'unpaid'),
                '签到状态': reg.get('checkin_status', 'unchecked'),
                '报名时间': reg.get('created_at', '') or '',
                '活动ID': reg.get('activity_id', 0),
            })
        return self.batch_create_records(table_id, records)

    def sync_customers(self, table_id, customers_data):
        if not customers_data:
            return {'ok': True, 'total': 0, 'batches': 0}
        records = []
        for cust in customers_data:
            records.append({
                '姓名': cust.get('name', ''),
                '手机号': cust.get('phone', '') or '',
                '微信号': cust.get('wechat', '') or '',
                '来源渠道': cust.get('source_channel', '') or '',
                '累计参与': cust.get('total_participations', 1),
                '创建时间': cust.get('created_at', '') or '',
            })
        return self.batch_create_records(table_id, records)
