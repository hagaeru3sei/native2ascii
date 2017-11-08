import gulp from 'gulp'
import browserify from 'browserify'
import source from 'vinyl-source-stream'
import transform from 'vinyl-transform'
//import uglify from 'gulp-uglify'

gulp.task('default', () => {
  console.log('Build command > gulp build')
});

gulp.task('build', () => {
  const browserified = transform(filename => {
    browserify(filename).bundle()
  });
  // Build JS
  browserify('src/js/index.js', {
    paths: ['node_modules', 'src/js']
  }).bundle()
    .pipe(source('main.js'))
    .pipe(gulp.dest('./dist/js'));
  // Copy HTML
  gulp.src(['src/html/*.html'])
    .pipe(gulp.dest('./dist'))
});
