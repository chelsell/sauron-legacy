@(name: String)

var index = 0;

$("#extend_table-@name").click(function () {
	index++;
	var newId = "extendable_row-@name-" + index;
	$("#extendable_row-@name").clone().attr("id", newId).appendTo("#extendable_table-@name");
	$("#" + newId + " :input").each(function (i, x) {
		var inputId = x.id.substring(0, x.id.lastIndexOf('-')) + '-' + index;
		$(x).attr('id', inputId);
	});
});
