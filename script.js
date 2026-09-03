document.addEventListener('DOMContentLoaded', function () {
  // Home "Gallery" grid: shuffle into a new order every load.
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

  // Gallery filter dropdown — values are "gear:leica", "gallery:nature", etc.
  var galleryFilter = document.getElementById('galleryFilter');
  if (galleryFilter && homeGallery) {
    galleryFilter.addEventListener('change', function () {
      var value = galleryFilter.value;
      var tiles = homeGallery.querySelectorAll('.tile');
      tiles.forEach(function (tile) {
        var match = value === 'all';
        if (!match && value.indexOf('gear:') === 0) {
          match = tile.getAttribute('data-gear') === value.slice(5);
        } else if (!match && value.indexOf('gallery:') === 0) {
          match = tile.getAttribute('data-gallery') === value.slice(8);
        }
        tile.style.display = match ? '' : 'none';
      });
    });
  }

  // Carousel — slides are pre-rendered by build_galleries.py from
  // photos/featured/, in that folder's order (not random). This just
  // handles the auto-advance and the dot indicators.
  var track = document.getElementById('carouselTrack');
  var dotsWrap = document.getElementById('carouselDots');
  if (track && dotsWrap) {
    var slideEls = track.querySelectorAll('.carousel-slide');
    dotsWrap.innerHTML = '';
    slideEls.forEach(function () { dotsWrap.appendChild(document.createElement('span')); });
    var dotEls = dotsWrap.querySelectorAll('span');
    var idx = Array.prototype.findIndex.call(slideEls, function (s) { return s.classList.contains('current'); });
    if (idx < 0) idx = 0;
    if (dotEls[idx]) dotEls[idx].classList.add('current');

    if (slideEls.length > 1) {
      setInterval(function () {
        slideEls[idx].classList.remove('current');
        dotEls[idx].classList.remove('current');
        idx = (idx + 1) % slideEls.length;
        slideEls[idx].classList.add('current');
        dotEls[idx].classList.add('current');
      }, 4000);
    }
  }

  // Click-to-expand lightbox — every photo on every page (including the
  // combined home "Gallery" grid) expands to its real, un-cropped shape.
  var lightboxImgs = document.querySelectorAll('.gallery-grid .tile-img');
  if (lightboxImgs.length) {
    var lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    var lightboxImg = document.createElement('img');
    lightbox.appendChild(lightboxImg);
    document.body.appendChild(lightbox);

    lightboxImgs.forEach(function (img) {
      img.addEventListener('click', function () {
        lightboxImg.src = img.src;
        lightbox.classList.add('open');
      });
    });
    lightbox.addEventListener('click', function () { lightbox.classList.remove('open'); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') lightbox.classList.remove('open');
    });
  }
});
