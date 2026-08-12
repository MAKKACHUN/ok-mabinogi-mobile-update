class DNAOneTimeTask:

    def run(self):
        if hasattr(self.executor.interaction, 'activate'):
            self.executor.interaction.activate()
        self.sleep(0.5)
        self.setup_fidget_action()
