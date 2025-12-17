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

def check_against_ignores(commitinfo)
	@ignore_tickets.each { |t|
		return false if commitinfo[2].include? t
	}
	commitinfo[3].each { |f|
		fname = f.split("/")[-1]
		unless @ignore_files.include? fname
			return true
		end
	}
	return false
end

@ignore_files = [ 
	"real_time_checks.asciidoc", # on hold
	"real_time_checks_enable.png", # on hold
	"real_time_checks_agent_rule.png", # on hold
	"real_time_checks_cpu_load_graph.png", # on hold
	"real_time_checks_rrd_config.png", # on hold
	"real_time_checks_service_overview.png", # on hold
	"internal_reference.asciidoc", # only of use in master
	"release_notes.asciidoc", # already diverting
]
@ignore_tickets = [
	"KNW-1934", # Documentation of cmk services
	"KNW-1943", # Documentation of cmk services typo
	"KNW-1959", # InfluxDB 3 is not supported
	"KNW-1967", # Translation of various articles after inserting new design elements
]
@ignore_commits = [

]

# Force these tickets to behave like pick-24
# Add a comment to each ticket to make cleaning easier later
@force_tickets = [
	"KNW-9999", # Example: Mattias is working on this...
]

pickbranches = [ "2.4.0" ]
missingcommits = {}
@allfiles = []
# Hold all files with already skipped commits, these should not pick as default
@files_with_skipped_commits = []
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
		@allfiles.push c[3]
		puts "#{c[0]} + #{c[1]} + #{c[2]}"
		nskipped = 0
		c[3].each { |f|
			s = ""
			if @files_with_skipped_commits.include? f
				s = " <= has skipped commits!"
				nskipped += 1
			end
			puts "    #{f}#{s}"
		}
		if check_against_ignores(c)
			if nskipped > 0
				defdec = "n"
				puts "===> Try to pick? [N/y] "
			else
				defdec = "y"
				puts "===> Try to pick? [Y/n] "
			end
			decision = gets
			decision = defdec if decision.strip == ""
			if decision.strip =~ /^y/i
				ret = system("git cherry-pick #{c[1]}")
				unless ret
					puts "+++> Pick failed. Abort the commit and continue loop or exit? [E/a] "
					secdec = gets
					if secdec.strip == "" || secdec.strip =~ /^e/
						exit 1
					else
						c[3].each { |f| @files_with_skipped_commits.push f }
						unless system("git cherry-pick --abort")
							exit 1
						end
					end
				end
			else
				c[3].each { |f| @files_with_skipped_commits.push f }
			end
		else
			puts "===> No decision needed, ticket or files on ignore list."
			c[3].each { |f| @files_with_skipped_commits.push f }
		end
    }
}

#~ @allfiles = @allfiles.sort.uniq

#~ puts "All files currently not in sync:"
#~ @allfiles.each { |f|
	#~ puts f
#~ }
