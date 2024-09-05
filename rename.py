import os

for i in os.walk('data'):
	path = i[0]
	if '&amp;' in path:
		os.rename(path, path.replace('&amp;', '&'))
