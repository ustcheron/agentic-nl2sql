import gradio as gr
import os
import json
from datetime import datetime
from pathlib import Path

def get_projects_dir():
    """获取项目目录路径"""
    # 获取项目根目录（webui的上级目录）
    current_dir = Path(__file__).parent.parent.parent
    return current_dir / "projects"

def ensure_projects_dir():
    """确保projects目录存在"""
    projects_dir = get_projects_dir()
    if not projects_dir.exists():
        projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir

def get_existing_projects():
    """获取现有项目列表"""
    projects_dir = get_projects_dir()
    if not projects_dir.exists():
        return []
    
    projects = []
    for item in projects_dir.iterdir():
        if item.is_dir():
            # 检查是否有项目配置文件
            config_file = item / "project_config.json"
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        projects.append({
                            'name': item.name,
                            'description': config.get('description', ''),
                            'created_time': config.get('created_time', '')
                        })
                except:
                    # 如果配置文件损坏，仍然显示项目名
                    projects.append({
                        'name': item.name,
                        'description': '配置文件损坏',
                        'created_time': ''
                    })
            else:
                # 没有配置文件的目录也显示
                projects.append({
                    'name': item.name,
                    'description': '无配置文件',
                    'created_time': ''
                })
    
    return sorted(projects, key=lambda x: x['name'])

def create_project(project_name, project_description):
    """创建新项目"""
    if not project_name or not project_name.strip():
        return "❌ 项目名称不能为空", gr.update(), gr.update(), gr.update()
    
    project_name = project_name.strip()
    
    # 检查项目名称是否合法（不包含特殊字符）
    if not project_name.replace('_', '').replace('-', '').replace(' ', '').isalnum():
        return "❌ 项目名称只能包含字母、数字、下划线和连字符", gr.update(), gr.update(), gr.update()
    
    # 确保projects目录存在
    projects_dir = ensure_projects_dir()
    
    # 检查项目是否已存在
    project_path = projects_dir / project_name
    if project_path.exists():
        return f"❌ 项目 '{project_name}' 已存在", gr.update(), gr.update(), gr.update()
    
    try:
        # 创建项目目录
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 创建项目配置文件
        config = {
            'name': project_name,
            'description': project_description.strip() if project_description else '',
            'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0'
        }
        
        config_file = project_path / "project_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 创建基本目录结构
        (project_path / "experiments").mkdir(exist_ok=True)
        (project_path / "data").mkdir(exist_ok=True)
        (project_path / "models").mkdir(exist_ok=True)
        (project_path / "logs").mkdir(exist_ok=True)
        
        # 创建README文件
        readme_content = f"""# {project_name}

## 项目描述
{project_description if project_description else '暂无描述'}

## 创建时间
{config['created_time']}

## 目录结构
- `experiments/`: 实验配置和结果
- `data/`: 数据文件
- `models/`: 模型文件
- `logs/`: 日志文件

## 使用说明
在此添加项目的使用说明...
"""
        
        readme_file = project_path / "README_android.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 更新项目列表
        projects = get_existing_projects()
        project_choices = [p['name'] for p in projects]
        
        return (
            f"✅ 项目 '{project_name}' 创建成功！",
            gr.update(choices=project_choices, value=project_name if project_choices else None),
            gr.update(value=""),  # 清空项目描述输入框
            gr.update(value="")   # 清空项目名称输入框
        )
        
    except Exception as e:
        return f"❌ 创建项目失败: {str(e)}", gr.update(), gr.update(), gr.update()

def refresh_project_list():
    """刷新项目列表"""
    projects = get_existing_projects()
    project_choices = [p['name'] for p in projects]
    return gr.update(choices=project_choices, value=project_choices[0] if project_choices else None)

def get_project_info(selected_project, is_global=False):
    """获取选中项目的详细信息
    
    Args:
        selected_project: 选中的项目名称
        is_global: 是否为全局项目信息显示（True返回项目名称、路径、描述，False返回项目详情markdown）
    
    Returns:
        如果is_global为False，返回项目详情markdown文本
        如果is_global为True，返回(项目名称, 项目路径, 项目描述)元组
    """
    if not selected_project:
        if not is_global:
            return "请选择一个项目"
        return "**项目名称**: 未选择", "**项目路径**: -", "**项目描述**: -"
    
    # 项目名称就是选择的值
    project_name = selected_project
    
    # 获取项目路径
    projects_dir = get_projects_dir()
    project_path = projects_dir / project_name
    
    if not project_path.exists():
        if not is_global:
            return f"项目 '{project_name}' 不存在"
        return f"**项目名称**: {project_name}", f"**项目路径**: 项目不存在", "**项目描述**: -"
    
    config_file = project_path / "project_config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if not is_global:
                # 返回项目详情markdown
                info = f"""## 项目信息

**项目名称**: {config.get('name', project_name)}
**项目描述**: {config.get('description', '暂无描述')}
**创建时间**: {config.get('created_time', '未知')}
**项目路径**: `{project_path}`

### 目录结构
"""
                # 列出项目目录内容
                for item in sorted(project_path.iterdir()):
                    if item.is_dir():
                        info += f"- 📁 `{item.name}/`\n"
                    else:
                        info += f"- 📄 `{item.name}`\n"
                
                return info
            else:
                # 返回项目选择信息
                return (
                    f"**项目名称**: {config.get('name', project_name)}",
                    f"**项目路径**: {project_path}",
                    f"**项目描述**: {config.get('description', '暂无描述')}"
                )
            
        except Exception as e:
            if not is_global:
                return f"读取项目配置失败: {str(e)}"
            return (
                f"**项目名称**: {project_name}",
                f"**项目路径**: {project_path}",
                f"**项目描述**: 配置文件读取失败"
            )
    else:
        if not is_global:
            return f"项目 '{project_name}' 缺少配置文件"
        return (
            f"**项目名称**: {project_name}",
            f"**项目路径**: {project_path}",
            "**项目描述**: 无配置文件"
        )

def create_project_management_tab():
    """项目管理标签页
    
    该标签页用于管理实验项目和资源，包括：
    - 项目管理
    - 资源监控
    - 实验记录
    - 结果分析
    """
    with gr.Blocks() as tab:
        gr.Markdown("# 🗂️ 项目管理")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 📋 项目列表")
                
                # 获取现有项目
                projects = get_existing_projects()
                project_choices = [p['name'] for p in projects]
                
                project_dropdown = gr.Dropdown(
                    choices=project_choices,
                    value=project_choices[0] if project_choices else None,
                    label="选择项目",
                    info="选择要查看或管理的项目"
                )
                
                refresh_btn = gr.Button("🔄 刷新项目列表", variant="secondary")
                
                gr.Markdown("## ➕ 新建项目")
                
                project_name_input = gr.Textbox(
                    label="项目名称",
                    placeholder="输入项目名称（只能包含字母、数字、下划线和连字符）",
                    info="项目名称将作为文件夹名称"
                )
                
                project_desc_input = gr.Textbox(
                    label="项目描述",
                    placeholder="输入项目描述（可选）",
                    lines=3,
                    info="描述项目的目标和用途"
                )
                
                create_btn = gr.Button("🚀 创建项目", variant="primary")
                
                status_output = gr.Textbox(
                    label="状态",
                    interactive=False,
                    lines=2
                )
            
            with gr.Column(scale=2):
                gr.Markdown("## 📊 项目详情")
                
                project_info_output = gr.Markdown(
                    value="请选择一个项目查看详细信息" if not project_choices else get_project_info(project_choices[0])
                )
        
        # 事件绑定
        refresh_btn.click(
            fn=refresh_project_list,
            outputs=[project_dropdown]
        )
        
        create_btn.click(
            fn=create_project,
            inputs=[project_name_input, project_desc_input],
            outputs=[status_output, project_dropdown, project_desc_input, project_name_input]
        )
        
        project_dropdown.change(
            fn=get_project_info,
            inputs=[project_dropdown],
            outputs=[project_info_output]
        )
    
    return tab, get_project_info, project_dropdown 