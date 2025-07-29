$(document).ready(function() {
    'use strict';

    // Логика для мобильного меню
    if ($('.hamburger').length && $('.menu_mm').length) {
        var hamburger = $('.hamburger');
        var menu = $('.menu_mm');
        var menuClose = $('.menu_close');

        hamburger.on('click', function() {
            menu.addClass('active');
        });

        menuClose.on('click', function() {
            menu.removeClass('active');
        });
    }

    // Логика для панели поиска
    if ($('.search_icon').length && $('.search_panel').length) {
        $('.search_icon').on('click', function() {
            $('.search_panel').toggleClass('active');
        });
    }

    // Инициализация слайдера
    if ($(".home_slider").length) {
        $(".home_slider").owlCarousel({
            items: 1,
            loop: true,
            autoplay: true,
            nav: false,
            dots: false
        });
    }
});