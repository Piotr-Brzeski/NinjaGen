#
# ninjagen.py
# 
# Created by Piotr Brzeski on 2023-05-13.
# Copyright © 2023 Brzeski.net. All rights reserved.
#

import yaml
import sys
import os

intermediates_dir = os.path.join(os.getcwd(), 'Release/Intermediates')
products_dir = os.path.join(os.getcwd(), 'Release/Products')

def print_targets(targets):
	print('')
	print(targets)
	print('')
	for target_name in targets.keys():
		print('')
		print(target_name)
		print(targets[target_name])
		print('')

def to_bool(value):
	if isinstance(value, bool):
		return value
	if str(value).lower() in ['true', 'yes', '1']:
		return True
	return False

def get_rules(project_dictionary):
	setttings_dictionary = {}
	if 'settings' in project_dictionary:
		if 'base' in project_dictionary['settings']:
			setttings_dictionary |= project_dictionary['settings']['base']
		if 'configs' in project_dictionary['settings']:
			if 'Release' in project_dictionary['settings']['configs']:
				setttings_dictionary |= project_dictionary['settings']['configs']['Release']
	rules = {}
	compile_cpp_rule = 'g++ -c'
	if 'CLANG_CXX_LANGUAGE_STANDARD' in setttings_dictionary:
		compile_cpp_rule += ' -std=' + setttings_dictionary['CLANG_CXX_LANGUAGE_STANDARD']
	if to_bool(setttings_dictionary.get('GCC_WARN_PEDANTIC')):
		compile_cpp_rule += ' -pedantic'
	if to_bool(setttings_dictionary.get('GCC_TREAT_WARNINGS_AS_ERRORS')):
		compile_cpp_rule += ' -Werror'
	compile_cpp_rule += ' $flags -o $out $in'
	rules['compile_cpp'] = compile_cpp_rule
	rules['archive'] = 'ar rcs $out $in'
	rules['link'] = 'g++ -o $out $in'
	return rules

def load_target(name, dictionary, path):
	products_dir = os.path.join(os.getcwd(), 'Release/Products')
	dictionary['project_path'] = path
	if dictionary['type'] == 'library.static':
		dictionary['target_path'] = os.path.join(products_dir, 'lib' + name + '.a')
	if dictionary['type'] == 'tool':
		dictionary['target_path'] = os.path.join(products_dir, name)
	return dictionary

def source_files(target):
	files = []
	if 'sources' in target:
		for source in target['sources']:
			if source.get('buildPhase') == 'none':
				continue
			if 'path' in source:
				source_path = source['path']
				extension = os.path.splitext(source_path)[1]
				if extension.lower() in ['.cpp', '.cc']:
					if not os.path.isabs(source_path):
						source_path = os.path.join(os.path.split(target['project_path'])[0], source_path)
					files.append(source_path)
	return files

def get_object_path(source_path, prefix, object_dir):
	rel_path = os.path.relpath(source_path, prefix)
	new_path = os.path.join(object_dir, rel_path)
	return new_path + '.o'

def out_rules(project_dictionary, file):
	rules = get_rules(project_dictionary)
	for rule_name in rules.keys():
		file.write('rule ' + rule_name + '\n')
		file.write('  command = ' + rules[rule_name] + '\n\n')

def out_build(product, rule, sources, file):
	sources_list = ''
	for source in sources:
		sources_list += ' ' + source.replace(' ', '$ ')
	file.write('build ' + product.replace(' ', '$ ') + ': ' + rule + sources_list + '\n')

def out_build_with_flags(product, rule, sources, flags, file):
	out_build(product, rule, sources, file)
	if flags != '':
		file.write('  flags = ' + flags + '\n')


#############################

project_path = os.path.abspath('project.yml')
if len(sys.argv) > 1:
	project_path = os.path.abspath(sys.argv[1])
srcroot = os.path.split(project_path)[0]

with open(project_path, 'r') as file:
	project_dictionary = yaml.safe_load(file)

if 'targets' in project_dictionary:
	targets = project_dictionary['targets']
	for target_name in targets.keys():
		targets[target_name] = load_target(target_name, targets[target_name], project_path)
else:
	targets = {}

if 'include' in project_dictionary:
	for include_path in project_dictionary['include']:
		if not os.path.isabs(include_path):
			include_path = os.path.join(os.path.split(project_path)[0], include_path)
		with open(include_path, 'r') as file:
			included_dictionary = yaml.safe_load(file)
			if 'targets' in included_dictionary:
				included_targets = included_dictionary['targets']
				for target_name in included_targets.keys():
					target_dictionary = included_targets[target_name]
					targets[target_name] = load_target(target_name, target_dictionary, include_path)

# print_targets(targets)

with open('build.ninja', 'w') as ninja_file:
	out_rules(project_dictionary, ninja_file)
	for target_name in targets.keys():
		object_dir = os.path.join(os.getcwd(), 'Release/Intermediates', target_name)
		target = targets[target_name]
		cpp_sources = source_files(target)
		path_prefix = ''
		if len(cpp_sources) > 1:
			path_prefix = os.path.commonpath(cpp_sources)
		else:
			path_prefix = os.path.split(cpp_sources[0])[0]
		flags = ''
		if 'settings' in target:
			settings = target['settings']
			if 'HEADER_SEARCH_PATHS' in settings:
				flags = '-I"' + settings['HEADER_SEARCH_PATHS'].replace('${SRCROOT}', srcroot) + '"'
		dependencies = []
		for cpp_source in cpp_sources:
			object_path = get_object_path(cpp_source, path_prefix, object_dir)
			dependencies.append(object_path)
			out_build_with_flags(object_path, 'compile_cpp', [cpp_source], flags, ninja_file)
		if 'dependencies' in target:
			for dependency in target['dependencies']:
				if to_bool(dependency.get('link')):
					dependency_path = targets[dependency['target']]['target_path']
					dependencies.append(dependency_path)
		if target['type'] == 'library.static':
			out_build(target['target_path'], 'archive', dependencies, ninja_file)
		if target['type'] == 'tool':
			out_build(target['target_path'], 'link', dependencies, ninja_file)
