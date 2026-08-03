document.addEventListener('DOMContentLoaded', function () {
  var chips = document.querySelectorAll('.chip');
  var tiles = document.querySelectorAll('.tile');

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) { c.classList.remove('active'); });
      chip.classList.add('active');

      var filter = chip.getAttribute('data-filter');
      tiles.forEach(function (tile) {
        var match = filter === 'all' || tile.getAttribute('data-gear') === filter;
        tile.style.display = match ? '' : 'none';
      });
    });
  });
});
