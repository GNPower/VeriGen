import os
import jinja2


def generate_templates(project_data, project_base_dir, output_dir, user_params):
    template_loader = jinja2.FileSystemLoader(searchpath=project_base_dir)
    template_env = jinja2.Environment(loader=template_loader, trim_blocks=True, lstrip_blocks=True)
    for template_info in project_data['templates']:
        source_path = template_info['source']
        dest_template = template_info['destination']
        rendered_dest_filename = template_env.from_string(dest_template).render(user_params)
        full_dest_path = os.path.join(output_dir, rendered_dest_filename)
        os.makedirs(os.path.dirname(full_dest_path), exist_ok=True)
        template = template_env.get_template(source_path)
        output_code = template.render(user_params)
        with open(full_dest_path, 'w') as f:
            f.write(output_code)