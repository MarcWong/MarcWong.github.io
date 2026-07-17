jQuery(document).ready(function($) {

    $('.level-bar-inner').css('width', '0');
    
    $(window).on('load', function() {

        $('.level-bar-inner').each(function() {
        
            var itemWidth = $(this).data('level');
            
            $(this).animate({
                width: itemWidth
            }, 800);
            
        });

    });

    var lightbox = document.getElementById('memories-lightbox');

    if (lightbox) {

        var lightboxImage = lightbox.querySelector('.lightbox-image');
        var lightboxCaption = lightbox.querySelector('.lightbox-caption');
        var photos = Array.prototype.slice.call(document.querySelectorAll('.memory-card img'));
        var currentIndex = 0;

        var showPhoto = function(index) {
            if (photos.length === 0) return;
            currentIndex = (index + photos.length) % photos.length;
            var photo = photos[currentIndex];
            lightboxImage.src = photo.src;
            lightboxImage.alt = photo.alt;
            lightboxCaption.textContent = photo.alt;
            lightbox.classList.add('is-open');
            lightbox.setAttribute('aria-hidden', 'false');
        };

        var closeLightbox = function() {
            lightbox.classList.remove('is-open');
            lightbox.setAttribute('aria-hidden', 'true');
            lightboxImage.src = '';
        };

        photos.forEach(function(photo, index) {
            photo.addEventListener('click', function() {
                showPhoto(index);
            });
            photo.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    showPhoto(index);
                }
            });
        });

        lightbox.querySelector('.lightbox-prev').addEventListener('click', function() {
            showPhoto(currentIndex - 1);
        });
        lightbox.querySelector('.lightbox-next').addEventListener('click', function() {
            showPhoto(currentIndex + 1);
        });
        lightbox.querySelector('.lightbox-close').addEventListener('click', closeLightbox);

        lightbox.addEventListener('click', function(e) {
            if (e.target === lightbox) {
                closeLightbox();
            }
        });

        document.addEventListener('keydown', function(e) {
            if (!lightbox.classList.contains('is-open')) return;
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowLeft') showPhoto(currentIndex - 1);
            if (e.key === 'ArrowRight') showPhoto(currentIndex + 1);
        });

    }

});