import os
import os.path

def insert_in_file_list(entries, entry):
    adddir, addname = entry
    if os.path.splitext(addname)[1] != ".py":
        return

    index = 0
    for (dir, name) in entries:
        if name[0] > addname[0] or (name[0] == addname[0] and name[1] > addname[1]):
            entries.insert(index, entry)
            break
        index += 1

    if index == len(entries):
        entries.append(entry)

def get_shell_files(path):
    ret = []

    entries = os.listdir(path)
    for i in entries:
        if len(i) > 0 and i[0] == '.':
            continue

        if os.path.isdir(i):
            subret = get_shell_files(path + '/' + i)
            for j in subret:
                insert_in_file_list(ret, j)
        else:
            insert_in_file_list(ret, (path, i))

    return ret

if __name__ == '__main__':
    print 'Starting QT Lab environment...'
    filelist = get_shell_files('shell_plugins')
    for (dir, name) in filelist:
        filename = '%s/%s' % (dir, name)
        print 'Executing %s...' % (filename)
        execfile(filename)

