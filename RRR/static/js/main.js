// Image Slider 
jQuery(document).ready(function ($) {
    $('#slider-area').owlCarousel({
        loop: true,
        autoplay: true,
        responsive: {
            0: {
                items: 1
            },
            600: {
                items: 1
            },
            1000: {
                items: 1
            },
        }
    })
});

// Message Box fadeout
setTimeout(function () {
    $('#message').fadeOut('slow');
}, 4000);