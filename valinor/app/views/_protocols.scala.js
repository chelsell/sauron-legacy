@import kokellab.valar.core.Tables.TemplateAssaysRow
@import kokellab.valar.core.Tables.TemplateStimulusFramesRow
@import kokellab.valar.core.Tables.Batteries
@import kokellab.valar.params.assays.AssayParameters


@(assays: Seq[TemplateAssaysRow])


var paramsLookup = new Map()
@for(t <- assays) {
	paramsLookup[@t.id] = "@{
	AssayParameters.assayParams(t.id).map(_.usage).mkString("; ")
	}";
}


$('[name^=assay]').change( function() {
	var ind = this.id.substring(this.id.lastIndexOf('-') + 1);
	$('#params-' + ind).val(paramsLookup[this.value])
});

