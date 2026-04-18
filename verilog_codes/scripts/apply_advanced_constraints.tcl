# Apply advanced MCMM-ready constraints to constrs_1.
# This script resolves paths relative to its own location, not Vivado's cwd.

if {[llength [get_projects -quiet]] == 0} {
    puts "ERROR: No project is open. Open SkyShield project first."
    return -code error
}

set script_dir [file dirname [file normalize [info script]]]
set root_dir   [file normalize [file join $script_dir ".."]]
set xdc_file   [file normalize [file join $root_dir "constraints" "cons_mcmm_advanced.xdc"]]

if {![file exists $xdc_file]} {
    puts "ERROR: Constraint file not found: $xdc_file"
    return -code error
}

set fs [get_filesets constrs_1]
if {[llength $fs] == 0} {
    puts "ERROR: Fileset constrs_1 not found."
    return -code error
}

set existing [get_files -quiet -of_objects $fs *cons_mcmm_advanced.xdc]
if {[llength $existing] == 0} {
    add_files -fileset constrs_1 $xdc_file
    puts "Added constraint file: $xdc_file"
} else {
    puts "Constraint entry already present in constrs_1."
}

# If Vivado uses an imported copy under .srcs/constrs_1/imports, sync it.
set existing [get_files -quiet -of_objects $fs *cons_mcmm_advanced.xdc]
foreach f $existing {
    set f_path [get_property NAME $f]
    if {$f_path eq ""} {
        set f_path $f
    }

    set src_norm [file normalize $xdc_file]
    set dst_norm [file normalize $f_path]

    if {$dst_norm ne $src_norm && [file exists $dst_norm]} {
        file copy -force $src_norm $dst_norm
        puts "Synchronized imported copy: $dst_norm"
    }

    set f_obj [get_files -quiet $f_path]
    if {[llength $f_obj] > 0} {
        set_property used_in_synthesis true $f_obj
        set_property used_in_implementation true $f_obj
    }
}

update_compile_order -fileset sources_1
puts "Advanced MCMM-ready constraints are applied."
puts "Constraint source: $xdc_file"
puts "Next: re-run synthesis/implementation, then run report_mcmm_advanced.tcl."
