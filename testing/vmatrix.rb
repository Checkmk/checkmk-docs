#!/usr/bin/env ruby

require 'json'

# Script to build an update/version matrix from supported_builds.json

distros = { 'ubuntu' => [], 'debian' => [], 'sles' => [], 'redhat'  => [] }

withdrawn = [ '2.1.0p7', '2.1.0p23', '2.2.0p10' ] # Manually add minor versions that have been withdrawn.
distroorder = [ 
    [ 'debian', 'jessie'], [ 'debian', 'stretch'], [ 'debian', 'buster'], [ 'debian', 'bullseye'], [ 'debian', 'bookworm'], 
    [ 'ubuntu', 'trusty'], [ 'ubuntu', 'xenial'], ['ubuntu', 'bionic'], ['ubuntu', 'cosmic'], ['ubuntu', 'disco'], ['ubuntu', 'eoan'], ['ubuntu', 'focal'], ['ubuntu', 'groovy'], ['ubuntu', 'hirsute'], ['ubuntu', 'impish'], ['ubuntu', 'jammy'], ['ubuntu', 'kinetic'], ['ubuntu', 'lunar'],
    [ 'redhat', 'el7'], [ 'redhat', 'el8'], [ 'redhat', 'el9'],
    [ 'sles', "sles12sp3"], [ 'sles', "sles12sp4"], [ 'sles', "sles12sp5"], [ 'sles', "sles15"], [ 'sles', "sles15sp1"], [ 'sles', "sles15sp2"], [ 'sles', "sles15sp3"], [ 'sles', "sles15sp4"], [ 'sles', "sles15sp5"]
]
releaseorder = [ '1.6.0', '2.0.0', '2.1.0', '2.2.0' ]
ignoreminors = []

# Get infile, outfile and versions to build the matrix from CLI arguments
infile = ARGV[0]
majors = ARGV[2].split ','
outfile = ARGV[1]
unless ARGV[3].nil?
    distros = {}
    ARGV[3].split(',').each { |f|
        distros[f] = []
    }
end

minors = {}
majors.each { |m| minors[m] = [] }

j = File.new(infile).read
h = JSON.parse(j)
minors.keys.each { |m|
    h['cre'][m].keys.reverse.each { |k| 
        puts k
        minors[m].push k unless minors[m].include?(k) || withdrawn.include?(k)
        distros.keys.each { |d|
            h['cre'][m][k][d].keys.reverse.each { |c|
                puts c
                if h['cre'][m][k][d][c] == 'supported'
                    distros[d].push c unless distros[d].include? c
                end
            }
        }
    }
}

nicenames = {
    'jessie' => 'Debian 8 _Jessie_',
    'stretch' => 'Debian 9 _Stretch_',
    'buster' => 'Debian 10 _Buster_',
    'bullseye' => 'Debian 11 _Bullseye_',
    'bookworm' => 'Debian 12 _Bookworm_',
    'trusty' => 'Ubuntu 14.04 LTS _Trusty Tahr_',
    'xenial' => 'Ubuntu 16.04 LTS _Xenial Xerus_',
    'bionic' => 'Ubuntu 18.04 LTS _Bionic Beaver_',
    'cosmic' => 'Ubuntu 18.10 _Cosmic Cuttlefish_',
    'eoan' => 'Ubuntu 19.10 _Eoan Ermine_',
    'disco' => 'Ubuntu 19.04 _Disco Dingo_',
    'focal' => 'Ubuntu 20.04 LTS _Focal Fossa_',
    'groovy' => 'Ubuntu 20.10 _Groovy Gorilla_',
    'hirsute' => 'Ubuntu 21.04 _Hirsute Hippo_',
    'impish' => 'Ubuntu 21.10 _Impish Indri_',
    'jammy' => 'Ubuntu 22.04 LTS _Jammy Jellyfish_',
    'kinetic' => 'Ubuntu 22.10 _Kinetic Kudu_',
    'lunar' => 'Ubuntu 23.04 _Lunar Lobster_',
    'el7' => 'Red Hat Enterprise Linux 7',
    'el8' => 'Red Hat Enterprise Linux 8',
    'el9' => 'Red Hat Enterprise Linux 9',
    "sles12sp3" => 'SUSE Linux Enterprise Server 12 SP3',
    "sles12sp4" => 'SUSE Linux Enterprise Server 12 SP4',
    "sles12sp5" => 'SUSE Linux Enterprise Server 12 SP5',
    "sles15" => 'SUSE Linux Enterprise Server 15',
    "sles15sp1" => 'SUSE Linux Enterprise Server 15 SP1',
    "sles15sp2" => 'SUSE Linux Enterprise Server 15 SP2',
    "sles15sp3" => 'SUSE Linux Enterprise Server 15 SP3',
    "sles15sp4" => 'SUSE Linux Enterprise Server 15 SP4',
    "sles15sp5" => 'SUSE Linux Enterprise Server 15 SP5',
}

distros.each { |k, v|
    v.each { |c|
        unless nicenames.has_key? c
            puts "Missing details for: #{c}"
            exit 1
        end
    }
    puts "#{k} #{v}"
}
minors.each { |k, v| puts "#{k} #{v}" }

# Retrieve the columns for each minor
releaseorder.each { |r|
    lastcolumn = []
    if minors.has_key? r
        minors[r].each { |m|
            thiscolumn = []
            distroorder.each { |d|
                if distros.has_key?(d[0])
                    if h['cre'][r][m][d[0]].has_key?(d[1]) && h['cre'][r][m][d[0]][d[1]] == 'supported'
                        thiscolumn.push 'supported'
                    else
                        thiscolumn.push ''
                    end
                end
            }
            if thiscolumn == lastcolumn
            ignoreminors.push m
            end
            lastcolumn = thiscolumn
        }
    end
}

# Print the matrix
outhandle = File.new(outfile, 'w')
# Table definition:
outhandle.write '[cols="5'
releaseorder.each { |r|
    if minors.has_key? r
        minors[r].each { |m|
            unless ignoreminors.include? m
                outhandle.write ',1'
            end
        }
    end
}
outhandle.write '"]'
outhandle.write "\n|===\n|Distribution "
# Table header:
releaseorder.each { |r|
    if minors.has_key? r
        minors[r].each { |m|
            unless ignoreminors.include? m
                outhandle.write "|#{m} "
            end
        }
    end
}
outhandle.write "\n\n"


distroorder.each { |d|
    supporteds = 0
    outrow = ''
    if distros.has_key?(d[0])
        outrow += "|#{nicenames[d[1]]}\n"
        releaseorder.each { |r|
            if minors.has_key? r
                minors[r].each { |m|
                    unless ignoreminors.include? m
                        if h['cre'][r][m][d[0]][d[1]] == 'supported'
                            outrow += "|icon:icon_confirm[alt=\"supported\"]\n"
                            supporteds += 1
                        else
                            outrow += "| \n"
                        end
                    end
                }
            end
        }
        outrow += "\n"
    end
    outhandle.write outrow if supporteds > 0
}
outhandle.write "|===\n"
outhandle.close
