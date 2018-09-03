import abc
import extern_libs

__metaclass__ = type

@extern_libs.add_metaclass(abc.ABCMeta)
class IScheduler:
    @abc.abstractmethod
    def execute_every(self, period, func):
        "execute func every period"
    
    @abc.abstractmethod
    def execute_at(self, when, func):
        "execute func at when"
    
    @abc.abstractmethod
    def execute_after(self, delay, func):
        "execute func after delay"
    
    @abc.abstractmethod
    def run_pending(self):
        "invoke the functions that are due"

class DefaultScheduler(extern_libs.InvokeScheduler, IScheduler):
    def execute_every(self, period, func):
        self.add(extern_libs.PeriodicCommand.after(period, func))
    
    def execute_at(self, when, func):
        self.add(extern_libs.DelayedCommand.at_time(when, func))
    
    def execute_after(self, delay, func):
        self.add(extern_libs.DelayedCommand.after(delay, func))