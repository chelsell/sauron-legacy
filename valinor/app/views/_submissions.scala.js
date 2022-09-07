@import kokellab.valar.core.Tables.TemplatePlatesRow
@import kokellab.valar.core.Tables.TemplateWellsRow
@import kokellab.valar.core.Tables.TemplateTreatmentsRow
@import kokellab.valar.core.Tables.ExperimentsRow
@import kokellab.utils.grammars.GrammarException
@import kokellab.valar.params.layouts.PreLayoutUtils


@(experiments: Seq[ExperimentsRow], templateWells: Seq[TemplateWellsRow], templateTreatments: Seq[TemplateTreatmentsRow])


// these MUST be changed here (last) or it will be ignored, even if !important is used
$('#protocol_parameters').css('font-family', 'monospace');
$('#well_parameters').css('font-family', 'monospace');
$('#treatment_parameters').css('font-family', 'monospace');


var fishParamsLookup = new Map()
@for(t <- experiments filter (_.templatePlateId.isDefined)) {
	fishParamsLookup[@t.id] = "@{
	try { PreLayoutUtils.listWellParams(t.templatePlateId.get).map(_.usage).mkString("\n") } catch { case e: GrammarException => s"————a error parsing the expression occurred————" }
	}";
}

var darkAdaptationLookup = new Map()
@for(t <- experiments filter (_.templatePlateId.isDefined)) {
	darkAdaptationLookup[@t.id] = "@{
		t.defaultAcclimationSec
}";
}

var treatmentParamsLookup = new Map()
@for(t <- experiments filter (_.templatePlateId.isDefined)) {
	treatmentParamsLookup[@t.id] = "@{
	try {PreLayoutUtils.listTreatmentParams(t.templatePlateId.get).map(_.usage).mkString("\n")} catch { case e: GrammarException => s"————a error parsing the expression occurred————" }
	}";
}

$('#experiment').change( function() {
	$('#well_parameters').val(fishParamsLookup[this.value]);
	$('#treatment_parameters').val(treatmentParamsLookup[this.value]);
	$('#acclimation_sec').val(darkAdaptationLookup[this.value]);
	$('#datetime_dosed').val(!(!treatmentParamsLookup[this.value].trim()));
});

