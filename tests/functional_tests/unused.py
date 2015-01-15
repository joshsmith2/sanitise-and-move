# Half written before os.path.exists epiphany. Might still come in handy

def test_do_not_move_resource_forks_if_not_set(self):
    fork_source = os.path.join(self.to_archive, 'forks')
    fork_container = os.path.join(fork_source, 'container')
    os.mkdir(fork_source)
    os.mkdir(fork_container)
    resource_files = ['._a.pdf', 'container/._hungbad.panc', '._.DS_Store']
    standard_files = ['a.pdf', 'container/gran._bag', 'pumpup._',]
    rf_paths = [os.path.join(fork_source, rf) for rf in resource_files]
    st_paths = [os.path.join(fork_source, sf) for sf in standard_files]
    all_paths = [].extend(rf_paths).extend(st_paths)

    # Create all the files we're about to move
    for ap in all_paths:
        with open (ap, 'w') as f:
            f.write('a')

    s = self.minimal_object()