from plumbum import local
l = local['luigi']
wrapper = l['--module', 'task', 'HepTask', '--test', True, '--local-scheduler']
print(wrapper())
