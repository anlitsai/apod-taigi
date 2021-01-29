name='apod-taigi'
# gitinit $name
# $name is the name of the repository

rm -rf .git/
git init
git remote add origin git@github.com:anlitsai/$name.git
git status
git add .
git commit -m "first commit"
git status
git push -u origin master
