#!/usr/bin/env ruby
# encoding: utf-8

require 'json'
require 'optparse'

def retrieve_commits() 
    commitlist = []
    IO.popen("git log --oneline --since #{@cfg["start_date"]}") { |l|
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
    ret = system("git checkout #{target}")
	raise "CheckoutFailed" unless ret
    system("git pull")
end

def check_against_ignores(commitinfo)
	@cfg["ignore_tickets"].each { |t|
		return false if commitinfo[2].include? t
	}
	commitinfo[3].each { |f|
		fname = f.split("/")[-1]
		unless @cfg["ignore_files"].include? fname
			return true
		end
	}
	return false
end

def get_config()
	@cfg = {
		"ignore_files" => [],
		"ignore_tickets" => [],
	}
	opts = OptionParser.new
	opts.on('--config', :REQUIRED) { |i|
		cfgfile = i
		@cfg = JSON.parse(File.read(cfgfile))
		@cfg['cfgfile'] = cfgfile
	}
	opts.on('--since', :REQUIRED) { |i| @cfg["start_date"] = i }
	opts.parse!
end

@cfg = {}

# Force these tickets to behave like pick-24
# Add a comment to each ticket to make cleaning easier later
# @force_tickets = [
# 	"KNW-9999", # Example: Mattias is working on this...
# ]

get_config
print @cfg

missingcommits = []
@allfiles = []
# Hold all files with already skipped commits, these should not pick as default
@files_with_skipped_commits = []

switch_branch @cfg["pick_from_branch"]
clist = retrieve_commits
switch_branch @cfg["pick_to_branch"]
olist = retrieve_commits

clist.each { |c|
    missingcommits.push c unless check_present(olist, c[0])
}

puts missingcommits 

missingcommits.reverse.each { |c|
	@allfiles.push c[3]
	puts "#{c[0]} + #{c[1]} + #{c[2]}"
	commitwords = c[2].gsub(',', ' ').split
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
		elsif commitwords.include? @cfg["keyword"]
			defdec = "y"
			puts "===> Try to pick? [Y/n] "
		else
			defdec = "n"
			puts "===> Try to pick? [N/y] "
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

#~ @allfiles = @allfiles.sort.uniq

#~ puts "All files currently not in sync:"
#~ @allfiles.each { |f|
	#~ puts f
#~ }
