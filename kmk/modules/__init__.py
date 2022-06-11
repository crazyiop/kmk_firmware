class InvalidExtensionEnvironment(Exception):
    pass


class Module:
    '''
    Modules differ from extensions in that they not only can read the state, but
    are allowed to modify the state. The will be loaded on boot, and are not
    allowed to be unloaded as they are required to continue functioning in a
    consistant manner.
    '''

    # The below methods should be implemented by subclasses

    def during_bootup(self, keyboard):
        return

    def before_matrix_scan(self, keyboard):
        '''
        Return value will be injected as an extra matrix update
        '''
        return

    def after_matrix_scan(self, keyboard):
        '''
        Return value will be replace matrix update if supplied
        '''
        return

    def process_key(self, keyboard, key, is_pressed, int_coord):
        return key

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return

    def on_powersave_enable(self, keyboard):
        return

    def on_powersave_disable(self, keyboard):
        return
