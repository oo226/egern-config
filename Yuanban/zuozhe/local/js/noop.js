// Local stub for upstream scripts that were removed upstream.
// Keeps module rules loadable without runtime errors.
const main = () => {
  if (typeof $done === 'function') $done();
  else if (typeof $task === 'object' && $task.fetch) $task.fetch('data:', {});
};
main();
