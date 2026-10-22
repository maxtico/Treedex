"""Dataset validation, persistence, synchronization and 20k-row preview coverage."""
import base64
from copy import deepcopy
import json
from time import perf_counter
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pandas as pd
from dash import Dash, no_update
import plotly.graph_objects as go
from treedex.data_manager import (make_dataset, apply_metadata, apply_columns, dataset_frame,
                                  dashboard_records, parse_upload, preview, association)
from treedex.data_callbacks import register_data_callbacks
from treedex.callbacks import register_callbacks
from treedex.layouts.main_layout import make_layout


class DataManagerTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame({'Species': ['a', 'b', 'c'], 'X': ['1', '2', None], 'Group': ['red', 'blue', 'red']})
        self.dataset = make_dataset(self.frame)
        self.app = Dash(__name__, suppress_callback_exceptions=True)
        self.app.layout = make_layout(self.frame, go.Figure())
        register_callbacks(self.app, self.frame, self.frame)
        register_data_callbacks(self.app, None)
        self.callbacks = {v['callback'].__wrapped__.__name__: v['callback'].__wrapped__
                          for v in self.app.callback_map.values() if 'callback' in v}

    def edit(self, trigger, dataset=None, **kwargs):
        with patch('treedex.data_callbacks.ctx', SimpleNamespace(triggered_id=trigger)):
            return self.callbacks['edit_dataset'](
                kwargs.get('contents'), 1, 1, 1, 1, kwargs.get('filename'),
                self.dataset if dataset is None else dataset, kwargs.get('name'),
                kwargs.get('metadata', self.dataset['columns']), kwargs.get('columns', self.dataset['columns']),
                kwargs.get('primary'), kwargs.get('key', 'Species'))

    def test_metadata_saved_exported_and_preserved_through_navigation(self):
        edits = deepcopy(self.dataset['columns'])
        edits[1].update(description='Body size', units='kg', role='measure', values='{"1": "Small"}')
        saved, _ = self.edit('save-data-metadata', metadata=edits)
        self.callbacks['switch_data_tab']('preview')
        self.callbacks['switch_data_tab']('metadata')
        restored = self.callbacks['describe_dataset'](saved)[5]
        self.assertEqual(restored[1]['description'], 'Body size')
        self.assertEqual(restored[1]['units'], 'kg')
        exported = self.callbacks['export_metadata'](1, saved)
        self.assertEqual(json.loads(exported['content'])['columns'][1]['values'], '{"1": "Small"}')
        self.assertNotIn('records', json.loads(exported['content']))
        self.assertEqual(self.dataset['columns'][1]['description'], '')
        edits[1]['values'] = '[1]'
        result, message = self.edit('save-data-metadata', metadata=edits)
        self.assertIs(result, no_update)
        self.assertIn('JSON object', message)

    def test_atomic_conversion_duplicate_names_and_identifiers(self):
        edits = deepcopy(self.dataset['columns'])
        edits[1].update(dtype='integer', name='Mass')
        saved = apply_columns(self.dataset, edits, 'Species', 'Species')
        self.assertEqual(str(dataset_frame(saved)['Mass'].dtype), 'Int64')
        self.assertEqual(saved['records'][0]['Mass'], 1)
        self.assertIsNone(saved['records'][2]['Mass'])
        self.assertIn('X', self.dataset['records'][0])
        for change in ({'dtype': 'boolean'}, {'name': 'Species'}, {'position': 1}, {'position': 1.5}):
            invalid = deepcopy(self.dataset['columns'])
            invalid[1].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                apply_columns(self.dataset, invalid, None, 'Species')
        for primary in ('X', 'Group'):
            with self.assertRaises(ValueError):
                apply_columns(self.dataset, self.dataset['columns'], primary, 'Species')
        fractional = make_dataset(pd.DataFrame({'Species': ['a'], 'X': [1.5]}))
        fractional['columns'][1]['dtype'] = 'integer'
        with self.assertRaises((ValueError, TypeError)):
            dataset_frame(fractional)

    def test_tree_key_rename_order_visibility_and_dashboard_sync(self):
        edits = deepcopy(self.dataset['columns'])
        edits[0].update(name='Taxon', position=3)
        edits[1].update(position=1, visible=False)
        edits[2]['position'] = 2
        saved = apply_columns(self.dataset, edits, 'Species', 'Species')
        self.assertEqual([c['name'] for c in saved['columns']], ['X', 'Group', 'Taxon'])
        rows, columns = dashboard_records(saved)
        self.assertEqual([r['Species'] for r in rows], ['a', 'b', 'c'])
        self.assertEqual(rows[0]['Taxon'], 'a')
        self.assertIn('2 / 3 rows matched', association(saved, ['a', 'b', 'd']))
        synced = self.callbacks['synchronize_dataset'](saved, self.dataset['records'], ['a'])
        self.assertEqual(synced[0], rows)
        self.assertEqual(synced[2:4], ([], []))
        self.assertNotIn('X', self.callbacks['describe_dataset'](saved)[-1])

    def test_renaming_preserves_built_plot_and_draft_column_references(self):
        edits = deepcopy(self.dataset['columns'])
        edits[1]['name'] = 'Mass'
        saved = apply_columns(self.dataset, edits, None, 'Species')
        options = {'x': 'X', 'y': ['X'], 'hover_data': ['X'], 'title': 'X', 'labels': '{"X": "Weight"}'}
        synced = self.callbacks['synchronize_dataset'](
            saved, self.dataset['records'], [], self.dataset['columns'],
            [{'id': 'plot_1', 'type': 'scatter', 'options': options}], options, {}, {'bar': options}, {})
        self.assertEqual(synced[4][0]['options']['x'], 'Mass')
        self.assertEqual(synced[6]['hover_data'], ['Mass'])
        self.assertEqual(synced[8]['bar']['y'], ['Mass'])
        self.assertEqual(synced[6]['title'], 'X')
        self.assertEqual(json.loads(synced[6]['labels']), {'Mass': 'Weight'})

    def test_delete_clears_linked_state_and_does_not_restore_initial_data(self):
        deleted, message = self.edit('delete-dataset')
        self.assertIsNone(deleted)
        rows, columns, selected_rows, selected, plots = self.callbacks['synchronize_dataset'](deleted, self.dataset['records'], ['a'])[:5]
        self.assertEqual((rows, columns, selected_rows, selected), ([], [], [], []))
        self.assertIsNone(plots[0]['type'])
        rendered = self.callbacks['render_managed_plots'](plots, [], [])
        self.assertIn('No dataset loaded', rendered.children)
        self.assertEqual(self.callbacks['describe_dataset'](None)[0], {})

    def test_csv_tsv_txt_uploads_and_datasets_without_species(self):
        for name, text in [('a.csv', 'Taxon,X\na,1\nb,2'), ('a.tsv', 'Taxon\tX\na\t1\nb\t2'), ('a.txt', 'Taxon;X\na;1\nb;2')]:
            contents = 'data:text/plain;base64,' + base64.b64encode(text.encode()).decode()
            saved, message = self.edit('upload-data', contents=contents, filename=name)
            self.assertEqual(len(saved['records']), 2)
            self.assertIsNone(saved['tree_key'])
            self.assertEqual(saved['columns'][1]['dtype'], 'integer')
            linked = apply_columns(saved, saved['columns'], 'Taxon', 'Taxon')
            self.assertEqual(dashboard_records(linked)[0][1]['Species'], 'b')
        with self.assertRaises(ValueError):
            make_dataset(pd.DataFrame([[1, 2]], columns=['X', ' X ']))
        failed, message = self.edit('upload-data', contents='data:;base64,bad', filename='a.csv')
        self.assertIs(failed, no_update)

    def test_rename_and_metadata_changes_keep_selection(self):
        renamed, _ = self.edit('rename-dataset', name='Measurements')
        self.assertEqual(renamed['name'], 'Measurements')
        result = self.callbacks['synchronize_dataset'](renamed, dashboard_records(renamed)[0], ['b'])
        self.assertIs(result[2], no_update)
        self.assertIs(result[3], no_update)

    def test_converted_data_builds_plots_and_selection_follows_renamed_tree_key(self):
        edits = deepcopy(self.dataset['columns'])
        edits[0]['name'] = 'Taxon'
        edits[1].update(name='Mass', dtype='integer')
        dataset = apply_columns(self.dataset, edits, None, 'Species')
        rows, _ = dashboard_records(dataset)
        with patch('treedex.callbacks.ctx', SimpleNamespace(triggered_id='build-scatter-plot')):
            instances, error, built = self.callbacks['build_plot'](
                scatter_clicks=1, pie_clicks=0, basic_clicks=0, selected_species=[],
                scatter_options={'x': 'Mass', 'y': 'Mass'}, pie_options={}, table_data=rows,
                built_plot=None, instances=[{'id': 'plot_1', 'type': None}], active_id='plot_1',
                pie_values=[], pie_ids=[], scatter_values=[], scatter_ids=[], selected_plot_type='scatter',
                basic_options={}, basic_values=[], basic_ids=[])
        self.assertEqual(error, '')
        self.assertEqual(built['options']['x'], 'Mass')
        cards = self.callbacks['render_managed_plots'](instances, ['b'], rows)
        figure = cards[0].children[1].children.figure
        self.assertEqual(list(figure.data[0].x)[:2], [1, 2])
        with patch('treedex.callbacks.ctx', SimpleNamespace(triggered_id='species-table')):
            selected, _ = self.callbacks['synchronize_selection'](None, [], [1], [], rows, [])
        self.assertEqual(selected, ['b'])

    def test_json_serialization_preserves_precision_dates_and_nulls(self):
        frame = pd.DataFrame({'Species': ['a', 'b'], 'Measurement': [1.2345678901234567, None],
                              'Date': pd.to_datetime(['2026-01-01', None])})
        dataset = make_dataset(frame)
        self.assertEqual(dataset['records'][0]['Measurement'], frame.Measurement[0])
        self.assertIsNone(dataset['records'][1]['Measurement'])
        self.assertIsNone(dataset['records'][1]['Date'])
        self.assertEqual(dataset_frame(dataset).Date[0], frame.Date[0])
        json.dumps(dataset, allow_nan=False)

    def test_preview_search_sort_and_20000_rows(self):
        big = make_dataset(pd.DataFrame({'Species': [f's{i}' for i in range(20000)], 'X': range(20000),
                                        'Group': ['a', 'b'] * 10000}))
        start = perf_counter()
        rows, pages, total = preview(big, 1, search='b', sort=[{'column_id': 'X', 'direction': 'desc'}])
        elapsed = perf_counter() - start
        self.assertEqual((len(rows), pages, total), (50, 200, 10000))
        self.assertEqual(rows[0]['X'], 19899)
        self.assertLess(len(json.dumps(rows)), 6000)
        self.assertLess(elapsed, 2.0)
        self.assertEqual(preview(big, search='[')[2], 0)
        print(f'\n20,000-row search/sort/page: {elapsed:.3f}s; page payload {len(json.dumps(rows)):,} bytes')

    def test_http_layout_and_dataset_mutation(self):
        client = self.app.server.test_client()
        for url in ('/', '/_dash-layout', '/_dash-dependencies'):
            self.assertEqual(client.get(url).status_code, 200)
        output, spec = next((k,v) for k,v in self.app.callback_map.items()
                            if 'callback' in v and v['callback'].__wrapped__.__name__ == 'edit_dataset')
        values = {'upload-data.contents': None, 'rename-dataset.n_clicks': 1,
                  'delete-dataset.submit_n_clicks': None, 'save-data-metadata.n_clicks': None,
                  'apply-data-columns.n_clicks': None, 'upload-data.filename': None,
                  'dataset-store.data': self.dataset, 'dataset-name-input.value': 'Renamed via HTTP',
                  'data-metadata-editor.data': self.dataset['columns'], 'data-columns-editor.data': self.dataset['columns'],
                  'data-primary-key.value': None, 'data-tree-key.value': 'Species'}
        def entry(item):
            return {'id': item['id'], 'property': item['property'], 'value': values[item['id'] + '.' + item['property']]}
        response = client.post('/_dash-update-component', json={
            'output': output, 'outputs': [{'id': o.component_id, 'property': o.component_property} for o in spec['output']],
            'inputs': [entry(x) for x in spec['inputs']], 'state': [entry(x) for x in spec['state']],
            'changedPropIds': ['rename-dataset.n_clicks']})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.json['response']['dataset-store']['data']['name'], 'Renamed via HTTP')


if __name__ == '__main__':
    unittest.main()
