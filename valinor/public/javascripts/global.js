// enable tooltips everywhere
$(function () {
	$('[data-toggle="tooltip"]').tooltip()
});

new Clipboard('.btn');

$(document).ready(function(){
    $('.collapse').on('show.bs.collapse', function (e) {
        $('.collapse').collapse("hide")
    })
});

