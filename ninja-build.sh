function quickbuild {
	ninja_bin="$ANDROID_BUILD_TOP/prebuilts/build-tools/linux-x86/bin/ninja"
	ninja_build_file="$ANDROID_BUILD_TOP/out/build-$TARGET_PRODUCT.ninja"
	if [ ! -f $ninja_build_file ]; then
		echo "can't find ninja build file $ninja_build_file"
		exit -1;
    fi

	if [ ! -f $ninja_bin ]; then
		echo "can't find ninja binary $ninja_bin"
		exit -1;
    fi

	$ninja_bin -f $ninja_build_file $1

}
