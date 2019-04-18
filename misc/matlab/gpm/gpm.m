function res = gpm(params)
% params.laser_ref  The #first scan $\frac{pi}{4}$#
% params.laser_sens
% params.maxAngularCorrectionDeg
% params.maxLinearCorrection
% params.sigma


	params_required(params, 'laser_sens');
	params_required(params, 'laser_ref');
	params = params_set_default(params, 'maxAngularCorrectionDeg', 25);
	params = params_set_default(params, 'maxLinearCorrection',    0.4);
	params = params_set_default(params, 'maxIterations',           20);
	params = params_set_default(params, 'sigma',                 0.01);
	params = params_set_default(params, 'interactive',  false);

	%% Compute surface orientation for \verb|params.laser_ref| and \verb|params.laser_sens|
	params = compute_surface_orientation(params);

	%% Number of constraints generated (total)
	k=1;

	%% \verb| ngenerated(a)|: number of constraints generated by point $a$ in \verb|laser_ref|.
	ngenerated = zeros(1, params.laser_ref.nrays);
	
	%% \verb|ngeneratedb(b)|: number of constraints generated by $b$ in \verb|laser_sens|.
	ngeneratedb = zeros(1, params.laser_sens.nrays);
	
	%% Iterate only on points which have a valid orientation.
	for j=find(params.laser_ref.alpha_valid)

		alpha_j = params.laser_ref.alpha(j);
		p_j = params.laser_ref.points(:,j);

		%% This finds a bound for the maximum variation of $\theta$ for 
		%% a rototranslation such that 
		%%  \[|t|\leq|t|_{\text{max}}=\verb|maxLinearCorrection|\]
		%% and
		%% \[|\varphi|\leq|\varphi|_{\text{max}}=\verb|maxAngularCorrectionDeg|\]
		%%  
		%% The bound is given by 
		%% \[ |\delta| \leq |\varphi|_{\text{max}} + \text{atan}{\frac{|t|_{\text{max}}}{|p_j|}}\]
	
		delta = abs(deg2rad(params.maxAngularCorrectionDeg)) + ...
		        abs(atan(params.maxLinearCorrection/norm(p_j)));
		
		angleRes = pi / size(params.laser_sens.points,2);
		range = ceil(delta/angleRes);
		from = j-range;
		to = j+range;
		from = max(from, 1);
		to   = min(to, size(params.laser_sens.points,2));
			
		
		for i=from:to
		
			if params.laser_sens.alpha_valid(i)==0
				continue;
			end
		
			alpha_i = params.laser_sens.alpha(i);
			phi = alpha_j - alpha_i;
			phi = normAngle(phi);
			
			if abs(phi) > deg2rad(params.maxAngularCorrectionDeg)
				continue
			end
			
			p_i = params.laser_sens.points(:,i);
			%% \newcommand{\fp}{\mathbf{p}}
			%% $\hat{T} = \fp_j - R_\phi \fp_j$
			T = p_j - rot(phi) * p_i;
			
	
			if norm(T) > params.maxLinearCorrection
				continue
			end
			
			weight=1;
			weight = weight * sqrt(params.laser_ref.alpha_error(j));
			weight = weight * sqrt(params.laser_sens.alpha_error(i));
			weight=sqrt(weight);
	
					
			C{k}.T = T;
			C{k}.phi = phi; 
			% Surface normal
			C{k}.alpha = alpha_j; 
			C{k}.weight = 1/weight;
			C{k}.i = i; 
			C{k}.j = j; 
			
			%% Keep track of how many generated particles per point
			ngenerated(j) = ngenerated(j) + 1;
			ngeneratedb(i) = ngeneratedb(i) + 1;
			%% Keep track of how many generated particles.
			k=k+1;
		end
	end
	
	%% Number of correspondences.
	N = size(C,2);
	fprintf('Number of corr.: %d\n', N);
	
	% build L matrix (Nx2) 
	L = zeros(N,2); L2 = zeros(2*N,3);
	Y = zeros(N,1); Y2 = zeros(2*N,1);
	W = zeros(N,1); W2 = zeros(2*N,1);
	Phi = zeros(N,1);
	samples = zeros(3,N);
	for k=1:N
		L(k,:) = vers(C{k}.alpha)';
		Y(k,1) = vers(C{k}.alpha)' * C{k}.T;
		W(k,1) = C{k}.weight;
		Phi(k,1) = C{k}.phi;
		block = [vers(C{k}.alpha)' 0; 0 0 1];
		L2((k-1)*2+1:(k-1)*2+2,1:3) = block;
		Y2((k-1)*2+1:(k-1)*2+2,1) = [Y(k,1); C{k}.phi]; 
		W2((k-1)*2+1:(k-1)*2+2,1) = [C{k}.weight;C{k}.weight];
		
		samples(:,k) = [C{k}.T; C{k}.phi];
	end
	
	theta = hill_climbing(Phi, W, deg2rad(20), mean(Phi), 20, deg2rad(0.001));
	fprintf('Theta: %f\n', rad2deg(theta));
	

	Inf3 = zeros(3,3);
	
	for k=1:N
		C{k}.v_alpha      = vers(C{k}.alpha);
		C{k}.v_dot_alpha  = vers(C{k}.alpha + pi/2);
		C{k}.R_phi        = rot(C{k}.phi);
		C{k}.R_dot_phi    = rot(C{k}.phi + pi/2);
		C{k}.v_j          = vers(params.laser_ref.theta(C{k}.j));
		C{k}.v_i          = vers(params.laser_sens.theta(C{k}.i)); 
		C{k}.cos_beta     = C{k}.v_alpha' * C{k}.v_i;
		C{k}.p_j          = params.laser_ref.points(:,C{k}.j);
		C{k}.p_i          = params.laser_sens.points(:,C{k}.i);
		C{k}.ngi          = 1; %ngeneratedb(C{k}.i);
		C{k}.ngj          = 1; %ngenerated(C{k}.j);
		
		sigma_alpha = deg2rad(6.4);
		sigma = params.sigma;
		noises = diag([C{k}.ngi*sigma_alpha^2 C{k}.ngj*sigma_alpha^2 ...
		              C{k}.ngi*sigma^2 C{k}.ngj*sigma^2]);

		n_alpha_i = -C{k}.v_alpha'*C{k}.R_dot_phi*C{k}.p_i;
		n_alpha_j = C{k}.v_dot_alpha'*(C{k}.T)+ C{k}.v_alpha'*C{k}.R_dot_phi*C{k}.p_i;
		n_sigma_i =  C{k}.v_alpha'* C{k}.R_phi * C{k}.v_i + C{k}.cos_beta;
		n_sigma_j =  - C{k}.v_alpha'*  C{k}.v_j;
		
		L_k = [C{k}.v_alpha' 0; 0 0 1];
		Y_k = [C{k}.v_alpha'*C{k}.T; C{k}.phi];
		M_k = [ n_alpha_i n_alpha_j n_sigma_i n_sigma_j; -1 1 0 0 ];
		R_k =  M_k * noises * M_k';
		C{k}.I = L_k' * inv(R_k) * L_k; 
		C{k}.M = L_k' * inv(R_k) * Y_k;
		Inf3 = Inf3 + C{k}.I;
	end
	
	Inf3
	Inf3(1:2,1:2)
	Cov = inv(Inf3(1:2,1:2));
	
	X = mean(samples,2);
	X2 = mean(samples,2);
	
%	X(3) = theta;
	for it=1:params.maxIterations
		fprintf(strcat(' X : ',pv(X),'\n'))
		fprintf(strcat(' X2: ',pv(X2),'\n'))
		Sigma = diag([0.5 0.5 deg2rad(40)].^2);
		
		M1 = zeros(3,3); M2 = zeros(3,1); block=zeros(3,2); by=zeros(2,1);
		T1 = zeros(3,3); T2 = zeros(3,1); 
		% update weights
		for k=1:N
			myX = [C{k}.T; C{k}.phi];
			weight = W(k,1) * mynormpdf( myX-X, [0;0;0], Sigma);
			%we =  exp(-norm(myX-X2));
			we = weight ;
			va = vers(C{k}.alpha);
			block = [va' 0; 0 0 1];
			by = [va' * C{k}.T; C{k}.phi];
			M1 = M1 + block' * weight * block;
			M2 = M2 + block' * weight * by;
			
			T1 = T1 + C{k}.I * we;
			T2 = T2 + C{k}.M * we;
		end
		Xhat = inv(M1) * M2;
		Xhat2 = inv(T1) * T2;
		
		delta = X-Xhat;
		delta = X2-Xhat2;
		X = Xhat;% X(3) = theta;
		X2 = Xhat2;
		if norm(delta(1:2)) < 0.00001
			break
		end
		pause(0.1)
	end
	
	res.X = X2;
	res.Phi = Phi;
	res.W = W;
	res.samples = samples;
	res.laser_ref=params.laser_ref;
	res.laser_sens=params.laser_sens;
	res.Inf = Inf;
	res.Cov = Cov;
	res.Cov3 = inv(Inf3);
	res.corr = C;
	
	
function p = mynormpdf(x, mu, sigma);
    mahal = (x-mu)' * inv(sigma) * (x-mu);    
	 p = (1 / sqrt(2*pi * det(sigma))) * exp(-0.5*mahal); % XXX
	 
function res = hill_climbing(x, weight, sigma, x0, iterations, precision)
% hill_climbing(x, weight, sigma, x0, iterations, precision)
	for i=1:iterations
		for j=1:size(x)
			updated_weight(j) =  weight(j) * mynormpdf(x(j), x0, sigma^2);
			%updated\_weight(j) =  weight(j) * exp( -abs(x(j)- x0)/ (sigma));
		end
		
		x0new = sum(x .* updated_weight') / sum(updated_weight);
		delta = abs(x0-x0new);
		x0 = x0new;
		
		fprintf(' - %f \n', rad2deg(x0));
		
		if delta < precision
			break
		end
	end
	
	res = x0;

function res = compute_surface_orientation(params)
	%% Find a parameter of scale
	n = params.laser_ref.nrays-1;
	for i=1:n
		dists(i) = norm( params.laser_ref.points(:,i)-params.laser_ref.points(:,i+1));
	end
	dists=sort(dists);
	
	%params.scale = mean(dists(n/2:n-n/5))*2;
	params.scale = max(dists(1:n-5))*2;
	fprintf('scale: %f\n', params.scale);
	
	if not(isfield(params.laser_ref, 'alpha_valid'))
		fprintf('Computing surface normals for ld1.\n');
		params.laser_ref = computeSurfaceNormals(params.laser_ref, params.scale);
	end
	
	if not(isfield(params.laser_sens, 'alpha_valid'))
		fprintf('Computing surface normals for ld2.\n');
		params.laser_sens = computeSurfaceNormals(params.laser_sens, params.scale);
	end
	
	res = params;
	