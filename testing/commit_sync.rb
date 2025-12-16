#!/usr/bin/env ruby
# encoding: utf-8

$startdate = '2025-08-01'

def retrieve_commits() 
    commitlist = []
    IO.popen("git log --oneline --since #{$startdate}") { |l|
        while l.gets
            ltoks = $_.split(' ', 2)
            cid = ltoks[0]
            cmsg = ltoks[1]
            cdt = ` git show -s --format='%aI %ae' #{cid} `.strip
            commitlist.push( [ cdt, cid, cmsg ] )
        end
    }
    commitlist.each { |c|
        IO.popen("git show --pretty="" --name-only #{c[1]}") { |l|
            files = []
            while l.gets
                files.push $_.strip
            end
            c.push files
        }
    }
    return commitlist
end

def check_present(commitlist, commitdate)
    commitlist.each { |c|
        return true if c[0] == commitdate
    }
    return false
end

def switch_branch(target)
    system("git checkout #{target}")
    system("git pull")
end

def check_against_ignores(filelist)
	relevant_files = 0
	filelist.each { |f|
		fname = f.split("/")[-1]
		unless @ignore_files.include? fname
			return true
		end
	}
	return false
end


@ignore_files = [ "real_time_checks.asciidoc",
	"real_time_checks_enable.png",
	"real_time_checks_agent_rule.png",
	"real_time_checks_cpu_load_graph.png",
	"real_time_checks_rrd_config.png",
	"real_time_checks_service_overview.png"
]
pickbranches = [ "2.4.0" ]
missingcommits = {}
pickbranches.each { |b| missingcommits[b] = [] }

switch_branch "master"
clist = retrieve_commits
switch_branch pickbranches[0]
olist = retrieve_commits

clist.each { |c|
    missingcommits[pickbranches[0]].push c unless check_present(olist, c[0])
}

missingcommits.each { |b,l|
    puts "#{b}:"
    l.reverse.each { |c|
		if check_against_ignores(c[3])
			puts "#{c[0]} + #{c[1]} + #{c[2]}"
			c[3].each { |f|
				puts "    #{f}"
			}
		end
    }
}
