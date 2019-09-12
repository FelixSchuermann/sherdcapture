function detect_sherd (folder, filename)
% According to
% https://de.mathworks.com/help/images/examples/color-based-segmentation-using-k-means-clustering.html?prodcode=IP&language=en
    fullpath = strcat(folder, '/images/', filename);
    he = imread(fullpath);
    %cform = makecform('srgb2lab');
    %lab_he = applycform(he,cform);
    hsv_he = rgb2hsv(he);
    %ab = double(lab_he(:,:,2:3));
    ab = double(hsv_he(:,:,2));
    nrows = size(ab,1);
    ncols = size(ab,2);
    ab = reshape(ab,nrows*ncols,1);
    
    clusters = 2;
    % repeat the clustering 3 times to avoid local minima
    [cluster_idx, ~] = kmeans(ab,clusters,'distance','sqEuclidean', ...
                                      'Replicates',3);
    binary_image = reshape(cluster_idx,nrows,ncols);
    
    % k-means labels 1 and 2, transform to 0 and 1
    % get the correct background label
    % we take three edgepoints assuming at least two were correctly
    % assigned
    background_label = mode([binary_image(1,1) binary_image(nrows,1) binary_image(1, ncols)]);
    binary_image(binary_image == background_label) = 0;
    binary_image(binary_image == background_label+1) = 1;
    
    
    % Remove small clusters from image
    smallest_object_size = round((nrows*ncols) / 50);

    binary_image = bwareaopen(binary_image, smallest_object_size);
    
    % Also remove small clusters from image
    % to remove holes in the object
    binary_image = ~binary_image;
    binary_image = bwareaopen(binary_image, smallest_object_size);
    
    % recover the original image
    binary_image = ~binary_image;
    
    %remove extension from filename and save image
    [~,name,ext] = fileparts(filename); 
    
    % create subfolder if neccessary
    masks_folder = strcat(folder, '/masks/');
    if ~exist(masks_folder, 'dir')
       mkdir(masks_folder);
    end
     imwrite(binary_image, strcat(masks_folder, name, '_mask', ext));
endfunction


