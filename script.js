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

  // Home page: shuffle the combined gallery into a new order every load.
  var homeGallery = document.getElementById('homeGallery');
  if (homeGallery) {
    var homeTiles = Array.prototype.slice.call(homeGallery.querySelectorAll('.tile'));
    for (var i = homeTiles.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var temp = homeTiles[i];
      homeTiles[i] = homeTiles[j];
      homeTiles[j] = temp;
    }
    homeTiles.forEach(function (tile) { homeGallery.appendChild(tile); });
  }
});
