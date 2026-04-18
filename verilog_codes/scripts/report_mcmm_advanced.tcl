# Advanced multi-corner reporting script (post-route recommended)

if {[llength [get_projects -quiet]] == 0} {
    puts "ERROR: No project is open."
    return -code error
}

# Open implemented design if available
set impl_run [get_runs -quiet impl_1]
if {[llength $impl_run] > 0} {
    open_run impl_1 -name impl_1
}

# Resolve output directory relative to this script location
set script_dir [file dirname [file normalize [info script]]]
set root_dir   [file normalize [file join $script_dir ".."]]
set rpt_dir    [file normalize [file join $root_dir "reports_mcmm"]]
file mkdir $rpt_dir

puts "Generating baseline timing/power/utilization reports..."
report_timing_summary -delay_type max -max_paths 20 -report_unconstrained -file [file join $rpt_dir timing_setup_summary.rpt]
report_timing_summary -delay_type min -max_paths 20 -report_unconstrained -file [file join $rpt_dir timing_hold_summary.rpt]
report_clock_interaction -file [file join $rpt_dir clock_interaction.rpt]
report_cdc -details -file [file join $rpt_dir cdc_report.rpt]
report_power -file [file join $rpt_dir power_mcmm_baseline.rpt]
report_utilization -hierarchical -file [file join $rpt_dir utilization_mcmm.rpt]

puts "Generating corner timing reports (tool-supported corner names)..."

# Corner names are tool/family dependent. Query valid names first.
set corner_names {}
if {[catch {set corner_names [get_speed_models -quiet]} msg]} {
    puts "INFO: get_speed_models query failed: $msg"
    set corner_names {}
}
set corner_names [lsort -unique $corner_names]

if {[llength $corner_names] == 0} {
    # Fallback: generate standard max/min reports without -corner
    puts "WARNING: Could not query named corners; writing max/min timing reports only."
    report_timing_summary -delay_type max -max_paths 20 -file [file join $rpt_dir timing_max_fallback.rpt]
    report_timing_summary -delay_type min -max_paths 20 -file [file join $rpt_dir timing_min_fallback.rpt]
} else {
    puts "Detected corners/speed models: $corner_names"
    foreach c $corner_names {
        set c_name [string map {" " "_" "/" "_" "\\" "_"} $c]
        if {[catch {
            report_timing_summary -corner $c -delay_type max -max_paths 20 -file [file join $rpt_dir timing_${c_name}_setup.rpt]
        } msg]} {
            puts "INFO: setup report skipped for corner '$c': $msg"
        }
        if {[catch {
            report_timing_summary -corner $c -delay_type min -max_paths 20 -file [file join $rpt_dir timing_${c_name}_hold.rpt]
        } msg]} {
            puts "INFO: hold report skipped for corner '$c': $msg"
        }
    }
}

puts "MCMM report generation complete."
puts "Output folder: $rpt_dir"
