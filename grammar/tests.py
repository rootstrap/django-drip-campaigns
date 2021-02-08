from pathlib import Path

from django.test import TestCase
from drip.models import Drip

from .parser import translate_query


class GrammarTest(TestCase):
    def test_grammar(self):
        grammar = Path(Path(__file__).parent, "grammar.lark").open()
        grammar = "".join(grammar.readlines())

        Drip(name="Nacho's Drip").save()
        Drip(name="Nice Drip").save()
        Drip(name="Not so nice").save()

        input_expression = "(enabled is False)" \
                           "and (sent_drips null True)" \
                           "and (name is \"Nacho's Drip\")"
        filter = translate_query(input_expression, grammar)
        assert Drip.objects.filter(**filter).count() == 1

        input_expression = "enabled is False"
        filter = translate_query(input_expression, grammar)
        assert Drip.objects.filter(**filter).count() == 3

        input_expression = "(enabled is False) and (name is \"Not so nice\")"
        filter = translate_query(input_expression, grammar)
        assert Drip.objects.filter(**filter).count() == 1

        input_expression = "(enabled is False) and (sent_drips null True)"
        filter = translate_query(input_expression, grammar)
        assert Drip.objects.filter(**filter).count() == 3

        input_expression = "(enabled is False) and (sent_drips null False)"
        filter = translate_query(input_expression, grammar)
        assert Drip.objects.filter(**filter).count() == 0
