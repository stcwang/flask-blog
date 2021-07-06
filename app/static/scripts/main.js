$(window).scroll(function () {
    var scroll = $(window).scrollTop();
    if (scroll > 0) {
        $(".nav-bar").addClass("active");
    } else {
        $(".nav-bar").removeClass("active");
    }
});