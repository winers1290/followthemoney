import os
import yaml
from unittest import TestCase
from followthemoney import model
from followthemoney.exc import InvalidMapping


class MappingTestCase(TestCase):

    def setUp(self):
        self.fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')

        db_path = os.path.join(self.fixture_path, 'kek.sqlite')
        os.environ['FTM_TEST_DATABASE_URI'] = 'sqlite:///' + db_path

        mapping_path = os.path.join(self.fixture_path, 'kek.yml')
        with open(mapping_path, 'r') as fh:
            self.kek_mapping = yaml.load(fh)

    def test_kek_map_single(self):
        mapping = model.make_mapping(self.kek_mapping)
        assert len(mapping.mappings) == 3, mapping.mappings
        assert len(mapping.refs) == 7, mapping.refs
        record = {
            'comp.id': 4,
            'sub.id': 7.4,
            'comp.name': 'Pets.com Ltd',
            'shares.share': '40%',
            'comp.url': 'https://pets.com',
            'sub.name': 'DogFood Sales Corp.',
            'comp.address': '10 Broadstreet, 20388 Washington, DC'
        }
        entities = mapping.map(record)
        assert len(entities) == 3, entities.keys()
        company = entities.get('company')
        assert company['id'], company
        assert record['comp.name'] in company['properties']['name'], company

    def test_kek_sqlite(self):
        entities = list(model.map_entities(self.kek_mapping))
        assert len(entities) == 8712, len(entities)
        ids = set([e['id'] for e in entities])
        assert len(ids) == 5599, len(ids)

    def test_csv_load(self):
        url = 'file://' + os.path.join(self.fixture_path, 'experts.csv')
        mapping = {'csv_url': url}
        with self.assertRaises(InvalidMapping):
            list(model.map_entities(mapping))
        mapping['entities'] = {
            'expert': {
                'schema': 'Person',
                'properties': {
                    'name': {'column': 'name'},
                    'nationality': {'column': 'nationality'},
                    'gender': {'column': 'gender'},
                }
            }
        }
        with self.assertRaises(InvalidMapping):
            list(model.map_entities(mapping))

        mapping['entities']['expert']['key'] = 'name'
        entities = list(model.map_entities(mapping))
        assert len(entities) == 14, len(entities)

        mapping['filters'] = {'gender': 'male'}
        entities = list(model.map_entities(mapping))
        assert len(entities) == 10, len(entities)

        mapping['filters_not'] = {'nationality': 'Portugal'}
        entities = list(model.map_entities(mapping))
        assert len(entities) == 7, len(entities)