$(document).ready(function () {
    var $rangeSlider = $('.range-slider');
    var $hiddenInput = $('input#price_filter');

    // Copy changes
    __rangeSlider_timer = false;
    function copyWithDelay() {
        if (__rangeSlider_timer) clearTimeout(__rangeSlider_timer);
        __rangeSlider_timer = setTimeout(function () {
            $hiddenInput.val($rangeSlider.val())
            $hiddenInput.trigger('change');
        }, 500)
    }

    var rangeValueBase = $rangeSlider.attr('value');
    if ($rangeSlider.length > 0) {
        $rangeSlider.each(function (index, value) {
            var rangeMin = $(this).data('range-min');
            var rangeMax = $(this).data('range-max');
            $(this).jRange({
                from: rangeMin,
                to: rangeMax,
                isRange: true,
                format: '%s €',
                ondragend: copyWithDelay,
                onbarclicked: copyWithDelay,
            });

            if ($('.navbar-collapse').css('display') == 'none') {
                $('.pointer-label.low').text(rangeMin + ' €')
                $('.pointer-label.high').text(rangeMax + ' €')

            }
        })
        var rangeValue;
        var rangeValueNew;
        $(window).resize(function () {
            rangeValue = $rangeSlider.attr('value');
            if (rangeValue !== 'NaN,NaN') {
                rangeValueNew = $rangeSlider.attr('value');
            }
            if (rangeValueNew == undefined) {
                $rangeSlider.jRange('setValue', rangeValueBase);
            }
            else {
                $rangeSlider.jRange('setValue', rangeValueNew);
            }
        })

        $('.navbar-toggler').click(function () {
            setTimeout(() => {
                if (rangeValueNew == undefined) {
                    $rangeSlider.jRange('setValue', rangeValueBase);
                }
                else {
                    $rangeSlider.jRange('setValue', rangeValueNew);
                }
            }, 200);
        })
    }
});
