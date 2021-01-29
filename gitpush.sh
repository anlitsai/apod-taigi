name='apod-taigi'
datetime=`date +%Y%m%d-%H%M`
comment='update_'$datetime
# gitpush.sh $name $comment
# $name is the name of the repository, $comment is commit message

git remote set-url origin git@github.com:anlitsai/$name.git
git status
git add .
git status
echo "git commit -m $comment"
git commit -m $comment
git push -f -u origin master
