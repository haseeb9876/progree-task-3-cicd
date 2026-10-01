import { validCategories } from '../../utils/constants.js';

// Deliberate failure on the demonstration branch only.
test('DEMO: incorrect category expectation must block deployment', () => {
  expect(validCategories).toContain('NotARealCategory');
});
