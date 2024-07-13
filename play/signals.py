from typing import List
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import GherkinRule, GherkinImpl

class GherkinRuleListener:
    from .game_rules_writer import GameRulesWriter as Naya
    naya = Naya()

    @receiver(post_save, sender=GherkinRule)
    def handle_post_save(sender, instance, created, **kwargs):
        """
        Whenever a Gherkin Rule is saved, search Gherkin Implementation.
        If not found, have GameRulesWriter write it.
        """
        RESERVED = ('given', 'when', 'then', 'and', 'but')

        def parse_rules(text):
            ret = []
            tracking = []
            for line in text.split('\n'):
                lowered = line.lower()
                if lowered.startswith('scenario'):
                    ret.append('\n'.join(tracking))
                    tracking = [line,]
                elif any(lowered.startswith(x) for x in RESERVED):
                    tracking.append(line)
            if tracking:
                ret.append('\n'.join(tracking))
            return ret

        def parse_lines(rule: List[str]):
            ret = set()
            for line in rule.split('\n'):
                if any(line.lower().startswith(x) for x in RESERVED):
                    ret.add(line)
            return list(ret)

        print('Signal received')

        rules = parse_rules(instance.gherkin)
        for rule in rules:
            lines = parse_lines(rule)
            tracking = 'given'
            for line in lines:
                lowered = line.lower()
                if not any(lowered.startswith(x) for x in (tracking, 'and', 'but')):
                    tracking = lowered.split(' ')[0]
                try:
                    impl = GherkinImpl.objects.get(gherkin_line=line)
                    print('Implementations for Gherkin Rule found')
                    print(impl.gherkin_line)
                    print(impl.gherkin_type)
                    print(impl.lambda_code)
                except GherkinImpl.DoesNotExist:
                    lambda_code = GherkinRuleListener.naya.write_lambda(rule, line, tracking)
                    payload = {
                        'gherkin_line': line,
                        'gherkin_type': tracking,
                        'lambda_code': lambda_code,
                    }
                    GherkinImpl.objects.create(**payload)
                    print('Implementations for Gherkin Rule created')
