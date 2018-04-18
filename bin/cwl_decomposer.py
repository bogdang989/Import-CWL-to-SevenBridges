"""
Usage:
    cwl_decomposer.py [options] (-t STR -a STR...) [-p STR]

Description:
    Install all apps from the workflow
    in the current project and link the workflow to those apps.

Options:

    -h, --help                    Show this message.

    -t STR                        Developer token.

    -p STR                        Platform (igor, cgc or gcp). [default: igor]

    -a STR...                     Workflow's app id (user-name/project-name/app-name[/rev_no])
"""

import sevenbridges as sbg
from sevenbridges.http.error_handlers import rate_limit_sleeper
from sevenbridges.http.error_handlers import maintenance_sleeper
from sevenbridges.http.error_handlers import general_error_sleeper
import sys
from docopt import docopt
import re


def init_api(dev_token, platform):
    """Initialize api for the platform used"""
    if platform == 'igor':
        api = sbg.Api(url="https://api.sbgenomics.com/v2", token=dev_token,
                      error_handlers=[rate_limit_sleeper, maintenance_sleeper, general_error_sleeper])
    elif platform == 'cgc':
        api = sbg.Api(url="https://cgc-api.sbgenomics.com/v2", token=dev_token,
                      error_handlers=[rate_limit_sleeper, maintenance_sleeper, general_error_sleeper])
    elif platform == 'gcp':
        api = sbg.Api(url="https://gcp-api.sbgenomics.com/v2", token=dev_token,
                      error_handlers=[rate_limit_sleeper, maintenance_sleeper, general_error_sleeper])
    else:
        raise ValueError('Platform not defined')
    return api


def replace_special_characters(string):
    return '-'.join([
                 x for x in filter(lambda x: x != '',
                                   re.sub('[^a-zA-Z0-9]', ' ', str(string).lower()).split(' '))])


def install_or_upgrade_app(step_id, project_id, raw_json, api):
    """Update the app if it exists, install it if not"""
    # Replace special characters in step id with -
    step_id = replace_special_characters(step_id)
    # Check if app exists in the project
    if len([a for a in api.apps.query(project=project_id).all() if a.id == '{}/{}'.format(project_id, step_id)]) == 1:
        existing_app = api.apps.get(api=api, id='{}/{}'.format(project_id, step_id))
        updated_app = existing_app.create_revision(id=existing_app.id, revision=existing_app.revision+1,
                                                   raw=raw_json)
    else:  # install the app if it does not exist
        updated_app = api.apps.install_app(id='{}/{}'.format(project_id, step_id), raw=raw_json)
    return updated_app


def breakdown_wf(wf_name, project_id, wf_json, api, installed_apps={}):
    """Go through all the steps (tools and nested workflows) and install them in the project.
    Link them to the main workflow.
    Update the main workflow"""

    for i, step in enumerate(wf_json['steps']):
        app_raw_dict = step['run']  # Raw app

        # Temporarily remove app name from json
        label_flag = False
        if 'label' in app_raw_dict:
            wf_app_label = app_raw_dict['label']
            label_flag = True
        try:  # Remove label, x and y keys from 'run' in sbg workflow if they exist
            del app_raw_dict['label']
            del app_raw_dict['x']
            del app_raw_dict['y']
        except KeyError:
            pass

        # Check if app is already installed and use existing app. Avoids making duplicate apps.
        if str(app_raw_dict) in installed_apps:
            installed_app = installed_apps[str(app_raw_dict)]
            step_json = installed_app.raw
            if label_flag:
                step_json['label'] = wf_app_label
            wf_json['steps'][i]['run'] = step_json
        else:
            # Get app name from original app
            if label_flag:  # For sbg apps use platform name
                try:
                    app_raw_dict['label'] = api.apps.get(app_raw_dict['sbg:id']).name
                except:
                    app_raw_dict['label'] = wf_app_label
            # For single tools install them and link them to the workflow.
            if app_raw_dict['class'] in ('CommandLineTool', 'ExpressionTool'):
                sys.stderr.write('Working on ' + step['id'] + '\n')
                new_app = install_or_upgrade_app(step['id'].lstrip('#'), project_id, app_raw_dict, api)
                if label_flag:
                    del app_raw_dict['label']
                installed_apps[str(app_raw_dict)] = new_app
                sys.stderr.write('Installing ' + new_app.raw['sbg:id'] + '\n')
                new_app_json = new_app.raw
                if label_flag:
                    new_app_json['label'] = wf_app_label
                wf_json['steps'][i]['run'] = new_app_json
            # For nested wfs: install all tools, install nested workflow then link to the main workflow.
            elif app_raw_dict['class'] == 'Workflow':
                new_app = breakdown_wf(step['id'].lstrip('#'), project_id, app_raw_dict, api, installed_apps)
                if label_flag:
                    del app_raw_dict['label']
                installed_apps[str(app_raw_dict)] = new_app
                new_app_json = new_app.raw
                if label_flag:
                    new_app_json['label'] = wf_app_label
                wf_json['steps'][i]['run'] = new_app_json

    # Update the workflow with modified json linked to new tools.
    updated_wf = install_or_upgrade_app(wf_name, project_id, wf_json, api)
    sys.stderr.write('Installing ' + updated_wf.raw['sbg:id'] + '\n')
    return updated_wf


def main():
    args = docopt(__doc__, version='1.0')

    dev_token = args['-t']
    platform = args['-p']
    wf_id_list = args['-a']  # list of workflows

    api = init_api(dev_token, platform)

    for wf_id in wf_id_list:
        project_id = '/'.join(wf_id.split('/')[:2])
        try:
            wf = api.apps.get(api=api, id=wf_id)
        except:
            raise ValueError("Invalid inputs. Workflow does not exist on the platform or your token is not correct.")
        breakdown_wf(wf_id.split('/')[2], project_id, wf.raw, api)


if __name__ == '__main__':
    sys.exit(main())
